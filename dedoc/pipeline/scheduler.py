import queue
import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from dedoc.pipeline.executor import LocalExecutor
from dedoc.pipeline.stage import Resource
from dedoc.pipeline.task import ExecMode, Task, TaskSpec, TaskState


@dataclass
class DocResult:
    """Result of running the task graph for one document."""
    tasks: List[Task] = field(default_factory=list)          # every task, in completion order (for debugging)
    warnings: List[str] = field(default_factory=list)
    by_id: Dict[str, Task] = field(default_factory=dict)

    def output(self, spec_name: str, page_number: int) -> Any:
        task = self.by_id.get(f"{spec_name}@p{page_number}")
        return None if task is None else task.output


# Routing: which worker pool runs a given spec.
#   GPU                     -> "gpu"          (single worker, batches same-type tasks)
#   CPU + ExecMode.PROCESS  -> "thread"       (task self-forks a subprocess, a thread just waits on it)
#   CPU + ExecMode.THREAD   -> "cpu_process"  (pure-Python task hosted in a process worker to beat the GIL)
def route(spec: TaskSpec) -> str:
    if spec.resource == Resource.GPU:
        return "gpu"
    return "thread" if spec.exec_mode == ExecMode.PROCESS else "cpu_process"


class Scheduler:
    """
    Blocker-graph scheduler for one document (Phase 1 core - executor-agnostic).

    For each page it instantiates one :class:`Task` per :class:`TaskSpec`; blocker edges are wired within a
    page from ``spec.blockers``. Tasks live in three sets - waiting / ready / done. A task becomes ready when
    all its blockers finish (a *failed* blocker still unblocks its dependents, which then receive the failed
    task's own input - pass-through). Ready tasks are dispatched to a free worker of the routed pool, picking
    the highest priority first (priority = depth in the graph, so work is rushed toward the GPU tasks) and,
    among equal priority, the lowest page number. GPU tasks of the same type are grouped into a batch that is
    flushed on ``batch_size`` or a timeout (so the last pages never stall).

    Phase 1 backs every pool with a thread pool for testing the scheduling logic; Phase 2 swaps the
    ``cpu_process`` pool for real persistent process workers and the ``gpu`` pool for the GPU worker.
    """

    def __init__(self, executor: Any = None, pool_sizes: Optional[Dict[str, int]] = None,
                 gpu_batch_timeout: float = 0.02, max_inflight_pages: int = 0, logger: Any = None) -> None:
        default_sizes = {"cpu_process": 4, "thread": 4, "gpu": 1, **(pool_sizes or {})}
        self.executor = executor if executor is not None else LocalExecutor(default_sizes)
        self.pool_sizes = self.executor.pool_sizes
        self.gpu_batch_timeout = max(0.0, gpu_batch_timeout)
        self.max_inflight_pages = max_inflight_pages  # <= 0 admits all pages at once; > 0 bounds pages in flight (memory)
        self.logger = logger

    def shutdown(self) -> None:
        self.executor.shutdown()

    def run(self, specs: List[TaskSpec], pages: List[int], seed: Callable[[int], Any],
            reduce_output: Optional[Callable[[Any], Any]] = None) -> DocResult:
        """
        :param specs: page-scope task specs (the per-page graph)
        :param pages: page numbers to process
        :param seed: ``seed(page_number) -> input`` for root tasks (those without blockers)
        :param reduce_output: optional ``fn(output) -> output`` applied to a task's retained output once every
            dependent has consumed it, to free large intermediate data (e.g. page images) on big documents
        """
        return _Run(self, specs, pages, seed, reduce_output).execute()


class _Run:
    def __init__(self, sched: Scheduler, specs: List[TaskSpec], pages: List[int], seed: Callable[[int], Any],
                 reduce_output: Optional[Callable[[Any], Any]] = None) -> None:
        self._sched = sched
        self._logger = sched.logger
        self._seed = seed
        self._reduce = reduce_output
        self._spec_by_name = {s.name: s for s in specs}
        self._priority = _compute_depths(specs)  # priority = depth in the blocker DAG

        self._tasks: Dict[str, Task] = {}
        self._pending: Dict[str, set] = {}       # task id -> set of blocker task ids not yet resolved
        self._dependents: Dict[str, List[str]] = {}  # task id -> ids that this task blocks
        self._resolved_inputs: Dict[str, dict] = {}  # task id -> {blocker_spec_name: value}
        self._build_graph(specs, pages)
        # free big intermediate outputs (page images) once every dependent has consumed them
        self._task_blockers = {tid: set(self._pending[tid]) for tid in self._tasks}
        self._dep_remaining = {tid: len(self._dependents[tid]) for tid in self._tasks}

        self._ready: List[Task] = []
        self._waiting = set(t.id for t in self._tasks.values())
        self._done: List[Task] = []
        self._warnings: List[str] = []

        self._executor = sched.executor
        self._sizes = sched.pool_sizes
        self._active = {name: 0 for name in self._sizes}     # busy worker slots per pool
        self._completions: "queue.Queue" = queue.Queue()
        self._gpu_first_ready: Dict[str, float] = {}          # gpu spec name -> monotonic time its oldest task became ready

        # windowed admission: only `max_inflight_pages` pages are seeded (e.g. rendered) at a time, bounding memory.
        # A page's root task(s) are seeded when the page is admitted; the next page is admitted when one finishes.
        self._page_remaining: Dict[int, int] = {}
        self._roots_by_page: Dict[int, List[str]] = {}
        for task in self._tasks.values():
            self._page_remaining[task.page_number] = self._page_remaining.get(task.page_number, 0) + 1
            if not self._pending[task.id]:
                self._roots_by_page.setdefault(task.page_number, []).append(task.id)
        self._pending_pages: List[int] = sorted(self._roots_by_page)
        self._inflight_pages = 0
        self._max_inflight = sched.max_inflight_pages if sched.max_inflight_pages > 0 else (len(self._pending_pages) or 1)
        self._admit_next_pages()

    def _admit_next_pages(self) -> None:
        while self._pending_pages and self._inflight_pages < self._max_inflight:
            page = self._pending_pages.pop(0)
            self._inflight_pages += 1
            for root_id in self._roots_by_page[page]:
                task = self._tasks[root_id]
                task.input = self._seed(page)  # seed (e.g. a render descriptor) is built lazily, only on admission
                self._make_ready(task)

    # ---- graph construction ----

    def _build_graph(self, specs: List[TaskSpec], pages: List[int]) -> None:
        for page in pages:
            for spec in specs:
                task = Task(spec=spec, page_number=page, priority=self._priority[spec.name])
                self._tasks[task.id] = task
                self._pending[task.id] = {f"{b}@p{page}" for b in spec.blockers}
                self._dependents[task.id] = []
                self._resolved_inputs[task.id] = {}
        for task in self._tasks.values():
            for blocker_id in self._pending[task.id]:
                self._dependents[blocker_id].append(task.id)

    # ---- main loop ----

    def execute(self) -> DocResult:
        total = len(self._tasks)
        while len(self._done) < total:
            self._dispatch()
            timeout = self._next_wait_timeout()
            try:
                poolname, tasks, future = self._completions.get(timeout=timeout)
            except queue.Empty:
                continue  # a GPU batch became ripe; loop back to dispatch it
            self._handle_completion(poolname, tasks, future)

        by_id = {t.id: t for t in self._done}
        return DocResult(tasks=list(self._done), warnings=self._warnings, by_id=by_id)

    def _dispatch(self) -> None:
        # 1) fill non-GPU pools with the best-ranked ready tasks
        for poolname in self._sizes:
            if poolname == "gpu":
                continue
            while self._active[poolname] < self._sizes[poolname]:
                task = self._pop_best_ready(poolname)
                if task is None:
                    break
                self._submit(poolname, [task])

        # 2) GPU pool: one batch of same-type tasks at a time
        if "gpu" in self._sizes and self._active["gpu"] < self._sizes["gpu"]:
            batch = self._pick_gpu_batch()
            if batch:
                self._submit("gpu", batch)

    def _pop_best_ready(self, poolname: str) -> Optional[Task]:
        best = None
        for task in self._ready:
            if route(task.spec) != poolname:
                continue
            if best is None or (task.priority, -task.page_number) > (best.priority, -best.page_number):
                best = task
        if best is not None:
            self._ready.remove(best)
        return best

    def _pick_gpu_batch(self) -> List[Task]:
        groups: Dict[str, List[Task]] = {}
        for task in self._ready:
            if route(task.spec) == "gpu":
                groups.setdefault(task.spec.name, []).append(task)
        if not groups:
            return []

        # choose the group with the most ready tasks, tie-broken by priority then page order
        name = max(groups, key=lambda n: (len(groups[n]), self._priority[n], -min(t.page_number for t in groups[n])))
        group = sorted(groups[name], key=lambda t: (-t.priority, t.page_number))
        batch_size = max(1, self._spec_by_name[name].batch_size)

        ripe = (time.monotonic() - self._gpu_first_ready.get(name, time.monotonic())) >= self._sched.gpu_batch_timeout
        no_more_coming = self._active_total() == 0 and not self._waiting and not self._other_ready_non_gpu(name)

        if len(group) >= batch_size or ripe or no_more_coming:
            chosen = group[:batch_size]
            for task in chosen:
                self._ready.remove(task)
            if any(route(t.spec) == "gpu" and t.spec.name == name for t in self._ready):
                self._gpu_first_ready[name] = time.monotonic()  # restart the timer for the leftover of this group
            else:
                self._gpu_first_ready.pop(name, None)
            return chosen
        return []

    def _other_ready_non_gpu(self, gpu_name: str) -> bool:
        return any(route(t.spec) != "gpu" for t in self._ready)

    def _active_total(self) -> int:
        return sum(self._active.values())

    def _next_wait_timeout(self) -> Optional[float]:
        # if a GPU group is ready but not yet dispatchable, wake up when it turns ripe
        if "gpu" in self._sizes and self._active["gpu"] < self._sizes["gpu"] and self._gpu_first_ready:
            oldest = min(self._gpu_first_ready.values())
            remaining = self._sched.gpu_batch_timeout - (time.monotonic() - oldest)
            return max(0.0, remaining)
        return None  # block until some worker reports back

    def _submit(self, poolname: str, tasks: List[Task]) -> None:
        for task in tasks:
            task.state = TaskState.RUNNING
        self._active[poolname] += 1
        future = self._executor.submit(poolname, tasks)
        future.add_done_callback(lambda f, p=poolname, ts=tasks: self._completions.put((p, ts, f)))

    def _handle_completion(self, poolname: str, tasks: List[Task], future: Future) -> None:
        self._active[poolname] -= 1
        error = future.exception()
        if error is None:
            for task, out in zip(tasks, future.result()):
                task.output, task.state = out, TaskState.DONE
        else:
            for task in tasks:
                task.output, task.state = None, TaskState.FAILED
                message = f"task {task.id} failed: {error.__class__.__name__}: {error}"
                self._warnings.append(message)
                if self._logger is not None:
                    self._logger.warning(message)

        for task in tasks:
            self._done.append(task)
            self._resolve_dependents(task)
            self._free_consumed_outputs(task)
            self._page_remaining[task.page_number] -= 1
            if self._page_remaining[task.page_number] == 0:
                self._inflight_pages -= 1
        self._admit_next_pages()  # a finished page frees a slot for the next one to be seeded/rendered

    def _free_consumed_outputs(self, task: Task) -> None:
        """Once a task has run, shrink the retained outputs whose data it (and every other dependent) no longer
        needs, so big intermediate page images do not pile up across a large document."""
        if self._reduce is None:
            return
        for blocker_id in self._task_blockers[task.id]:
            self._dep_remaining[blocker_id] -= 1
            if self._dep_remaining[blocker_id] == 0:
                blocker = self._tasks[blocker_id]
                if blocker.output is not None:
                    blocker.output = self._reduce(blocker.output)
        if self._dep_remaining[task.id] == 0 and task.output is not None:  # terminal task: nothing downstream needs it
            task.output = self._reduce(task.output)

    def _resolve_dependents(self, task: Task) -> None:
        # a failed task passes its own input through to dependents instead of an output
        value = task.input if task.state == TaskState.FAILED else task.output
        for dep_id in self._dependents[task.id]:
            self._resolved_inputs[dep_id][task.spec.name] = value
            self._pending[dep_id].discard(task.id)
            if not self._pending[dep_id]:
                dep = self._tasks[dep_id]
                resolved = self._resolved_inputs[dep_id]
                dep.input = next(iter(resolved.values())) if len(resolved) == 1 else dict(resolved)
                self._make_ready(dep)

    def _make_ready(self, task: Task) -> None:
        task.state = TaskState.READY
        self._waiting.discard(task.id)
        self._ready.append(task)
        if route(task.spec) == "gpu":
            self._gpu_first_ready.setdefault(task.spec.name, time.monotonic())


def _compute_depths(specs: List[TaskSpec]) -> Dict[str, int]:
    by_name = {s.name: s for s in specs}
    depth: Dict[str, int] = {}

    def visit(name: str, stack: frozenset) -> int:
        if name in depth:
            return depth[name]
        if name in stack:
            raise ValueError(f"cycle in task blockers involving '{name}'")
        blockers = by_name[name].blockers
        d = 0 if not blockers else 1 + max(visit(b, stack | {name}) for b in blockers)
        depth[name] = d
        return d

    for spec in specs:
        visit(spec.name, frozenset())
    return depth
