import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Iterable, List, Optional

from dedoc.pipeline.gpu_batcher import GpuBatcher
from dedoc.pipeline.stage import DocState, Resource, Stage


class Orchestrator:
    """
    Schedules a staged document pipeline for a single document.

    Page-scope stages form an ordered chain run per page: CPU stages run on a thread pool, GPU
    stages are routed to a per-stage dynamic batcher. A worker does **not** block while a page
    waits at the GPU - the page's continuation (its remaining stages) is resubmitted to the pool
    once the batch resolves, so the GPU batch size is decoupled from the CPU worker count.

    After every page has finished, document-scope stages run sequentially as barriers.

    Pages are consumed from a (possibly streaming) iterable; at most ``max_inflight`` pages are
    kept in flight at once to bound memory, which lets page rendering pipeline with processing.

    The orchestrator carries no cancellation token by design: cancellation (e.g. client disconnect)
    is handled out of process by terminating the whole worker process group.
    """
    def __init__(self, cpu_workers: int = 4, gpu_max_batch: int = 8, gpu_max_latency: float = 0.02,
                 max_inflight: Optional[int] = None, logger: Any = None) -> None:
        self.cpu_workers = max(1, cpu_workers)
        self.gpu_max_batch = max(1, gpu_max_batch)
        self.gpu_max_latency = max(0.0, gpu_max_latency)
        self.max_inflight = max_inflight if max_inflight is not None else max(self.cpu_workers, self.gpu_max_batch) * 2
        self.logger = logger

    def run(self, pages: Iterable[Any], page_stages: List[Stage], doc_stages: Optional[List[Stage]] = None, ctx: Any = None) -> DocState:
        active_page_stages = [stage for stage in page_stages if stage.is_enabled(ctx)]
        active_doc_stages = [stage for stage in (doc_stages or []) if stage.is_enabled(ctx)]
        return _Run(self, active_page_stages, active_doc_stages, ctx).execute(pages)


class _Run:
    """Holds the mutable state of one ``Orchestrator.run`` invocation (keeps the Orchestrator reentrant)."""
    def __init__(self, orch: Orchestrator, page_stages: List[Stage], doc_stages: List[Stage], ctx: Any) -> None:
        self._ctx = ctx
        self._page_stages = page_stages
        self._doc_stages = doc_stages
        self._logger = orch.logger
        self._pool = ThreadPoolExecutor(max_workers=orch.cpu_workers, thread_name_prefix="cpu-stage")
        self._batchers = {
            stage.name: GpuBatcher(stage.fn, ctx, orch.gpu_max_batch, orch.gpu_max_latency, orch.logger)
            for stage in page_stages if stage.resource == Resource.GPU
        }
        self._inflight = threading.Semaphore(orch.max_inflight)
        self._lock = threading.Lock()
        self._results: dict = {}
        self._submitted = 0
        self._completed = 0
        self._all_submitted = False
        self._done = threading.Event()

    def execute(self, pages: Iterable[Any]) -> DocState:
        try:
            for index, payload in enumerate(pages):
                self._inflight.acquire()  # backpressure: bound the number of pages in flight
                with self._lock:
                    self._submitted += 1
                self._pool.submit(self._run_from, index, payload, 0)
            with self._lock:
                self._all_submitted = True
                finished = self._completed == self._submitted
            if finished:
                self._done.set()
            self._done.wait()
            return self._finalize()
        finally:
            for batcher in self._batchers.values():
                batcher.shutdown()
            self._pool.shutdown(wait=True)

    def _run_from(self, index: int, payload: Any, start: int) -> None:
        try:
            i = start
            while i < len(self._page_stages):
                stage = self._page_stages[i]
                if stage.resource == Resource.GPU:
                    future = self._batchers[stage.name].submit(payload)
                    future.add_done_callback(lambda f, idx=index, pos=i: self._resume(idx, pos, f))
                    return  # release this worker; the continuation is resubmitted when the batch resolves
                payload = stage.fn(payload, self._ctx)
                i += 1
            self._on_done(index, payload, None)
        except Exception as error:
            self._on_done(index, None, error)

    def _resume(self, index: int, pos: int, future: Future) -> None:
        try:
            result = future.result()
        except Exception as error:
            self._on_done(index, None, error)
            return
        try:
            self._pool.submit(self._run_from, index, result, pos + 1)
        except RuntimeError as error:  # pool already shut down - should not happen before _done is set
            self._on_done(index, None, error)

    def _on_done(self, index: int, payload: Any, error: Optional[BaseException]) -> None:
        with self._lock:
            self._results[index] = (payload, error)
            self._completed += 1
            finished = self._all_submitted and self._completed == self._submitted
        self._inflight.release()
        if finished:
            self._done.set()

    def _finalize(self) -> DocState:
        pages_out: List[Any] = [None] * self._submitted
        warnings: List[str] = []
        for index in range(self._submitted):
            payload, error = self._results[index]
            if error is None:
                pages_out[index] = payload
            else:
                message = f"page {index} failed: {error.__class__.__name__}: {error}"
                warnings.append(message)
                if self._logger is not None:
                    self._logger.warning(message)
        state = DocState(pages=pages_out, warnings=warnings, ctx=self._ctx)
        for stage in self._doc_stages:
            returned = stage.fn(state)
            if returned is not None:
                state = returned
        return state
