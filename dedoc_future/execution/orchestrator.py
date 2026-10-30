from __future__ import annotations
import itertools
import logging
import threading
from concurrent.futures import Future
from dataclasses import dataclass
from queue import Empty, PriorityQueue
from typing import Literal

from tdm import TalismanDocument

from dedoc_future.abstract.blob_ref import NodeId
from dedoc_future.abstract.module import MergeModule, SplitModule
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.configs.runtime import RuntimeConfig
from dedoc_future.configs.runtime_plan import RuntimePlan
from dedoc_future.execution.blob_registry import BlobRegistry
from dedoc_future.execution.document_state import DocumentState, StepId
from dedoc_future.execution.subtask_tracker import SubtaskTracker
from dedoc_future.execution.task import SplitId, SubtaskSpec, Task, TaskId, TaskOutput
from dedoc_future.abstract.enums import TaskStatus
from dedoc_future.execution.worker_pools import WorkerPools
from dedoc_future.configs.system_config import SystemConfig


@dataclass
class ProcessingResult:
    doc: TalismanDocument
    status: Literal["ok", "failed"]

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    on_subtask_failure: Literal["abort_all", "skip_subtask", "fallback"] = "abort_all"
    on_dependency: Literal["fail", "cascade", "keep_and_warn"] = "fail"
    poll_timeout: float = 0.05


class Orchestrator:
    def __init__(
        self,
        system_config: SystemConfig,
        workers: WorkerPools,
        blob_registry: BlobRegistry,
        orchestrator_cfg: OrchestratorConfig | None = None,
    ):
        self.system_config = system_config
        self.workers = workers
        self.blobs = blob_registry
        self.cfg = orchestrator_cfg or OrchestratorConfig()
        self.tracker = SubtaskTracker(on_failure=self.cfg.on_subtask_failure)
        self._counter = itertools.count()
        self._lock = threading.Lock()
        self._inflight: dict[TaskId, Future] = {}

    def run(self, document: TalismanDocument, runtime_config: RuntimeConfig) -> ProcessingResult:
        plan = self.system_config.bind(runtime_config, document)
        state = DocumentState(document)
        queue: PriorityQueue[tuple[int, int, Task]] = PriorityQueue()
        failed = False

        for step in plan.initial_front:
            self._enqueue(queue, self._make_task(plan, step, state.doc, runtime_config))

        while not queue.empty() or self._inflight:
            try:
                _, _, task = queue.get(timeout=self.cfg.poll_timeout if self._inflight else None)
            except Empty:
                task = None
            if task is not None:
                self._dispatch(task)

            for tid, fut in list(self._inflight.items()):
                if not fut.done():
                    continue
                self._inflight.pop(tid)
                out = self._collect(fut, task_hint=None)
                if not self._handle_output(out, plan, state, queue, runtime_config):
                    failed = True

        status = "failed" if (failed or state.failed_steps) else "ok"
        return ProcessingResult(doc=state.doc, status=status)

    def _make_task(
        self,
        plan: RuntimePlan,
        step: StepId,
        source_doc: TalismanDocument,
        runtime_config: RuntimeConfig,
        *,
        parent: Task | None = None,
        spec: SubtaskSpec | None = None,
    ) -> Task:
        module = plan.steps[step]
        if spec is not None:
            base = parent.container.with_nodes(
                [parent.container.id2node[i] for i in spec.scope]
            )
            container = plan.build_container_for_module(spec.module_name, base)
            return Task(
                task_id=f"t{next(self._counter)}",
                step=plan.step_for_module(spec.module_name),
                module_name=spec.module_name,
                container=container,
                params=parent.params,
                split_id=self._split_id_for(parent),
                subtask_id=f"{self._split_id_for(parent)}#{spec.order}",
                priority=parent.priority,
            )

        container = plan.build_container(step, source_doc)
        local_params = runtime_config.get_for(module.name, self.system_config)
        return Task(
            task_id=f"t{next(self._counter)}",
            step=step,
            module_name=module.name,
            container=container,
            params=local_params,
            priority=0 if not module.blockers else 1,  # TODO
        )

    def _enqueue(self, queue: PriorityQueue, task: Task) -> None:
        queue.put((task.priority, next(self._counter), task))

    def _dispatch(self, task: Task) -> None:
        module = self.system_config.modules[task.module_name]
        processor_cls = getattr(module, "processor_cls", None) or getattr(module, "merger_cls", None)
        profile = processor_cls.resource_profile
        self._retain_container_blobs(task.container)
        fut = self.workers.pool_for(profile).submit(self._run_task, module, task)
        self._inflight[task.task_id] = fut

    @staticmethod
    def _run_task(module, task: Task) -> TaskOutput:
        try:
            processor = module.processor_cls(init_params=module.init_params)
            result = processor.process(task.container, task.params)
            return TaskOutput(task=task, result=result, status=TaskStatus.ok)
        except Exception as exc:
            logger.exception(f"Task failed: {task.task_id}", exc_info=exc)
            return TaskOutput(task=task, result=None, status=TaskStatus.failed)

    @staticmethod
    def _collect(fut: Future, *, task_hint: Task | None) -> TaskOutput:
        try:
            return fut.result()
        except Exception as exc:
            if task_hint is None:
                raise
            return TaskOutput(task=task_hint, result=None, status=TaskStatus.failed)

    def _handle_output(self, out: TaskOutput, plan, state, queue, params) -> bool:
        task = out.task
        if task.subtask_id is not None:
            self._on_subtask_done(out, plan, state, queue, params)
            return True

        if out.status == TaskStatus.failed:
            return self._handle_failure(task, plan, state, queue, params)

        module = self.system_config.modules[task.module_name]

        if isinstance(module, SplitModule):
            self._open_split(task, out, plan, queue, params)
            return True

        if isinstance(module, MergeModule):
            self._apply_merge(task, module, state, params)
            return True

        state.apply(task.step, self._scope_of(task.container), out.result)
        self._release_consumed(out.result)
        self._unlock_successors(task.step, plan, state, queue, params)
        return True

    def _open_split(self, task, out: TaskOutput, plan, queue, params) -> None:
        specs = out.subtasks or []
        split_id = self._split_id_for(task)
        self.tracker.open(split_id, len(specs))
        for spec in specs:
            self._enqueue(
                queue,
                self._make_task(plan, None, None, params, parent=task, spec=spec),
            )

    def _on_subtask_done(self, out: TaskOutput, plan, state, queue, params) -> None:
        split_id = out.task.split_id
        if self.tracker.complete(split_id, out):
            merge_step = plan.merge_for(split_id)
            self._enqueue(queue, self._make_task(plan, merge_step, state.doc, params))

    def _apply_merge(self, task, module: MergeModule, state, params) -> None:
        outputs = self.tracker.collect(task.split_id)
        merger = module.merger_cls(init_params=module.init_params)
        merged = merger.merge(task.container, [o.result for o in outputs if o.result])
        state.apply(task.step, self._scope_of(task.container), merged)
        self._release_consumed(merged)
        self._unlock_successors(task.step, self.system_config.plan_for(state), state, None, params) if False else None

    def _unlock_successors(self, step, plan, state, queue, params) -> None:
        for succ in plan.successors(step):
            if plan.is_ready(succ, state) and succ not in state.completed_steps:
                self._enqueue(queue, self._make_task(plan, succ, state.doc, params))

    def _handle_failure(self, task, plan, state, queue, params) -> bool:
        state.mark_failed(task.step)
        fb_step = plan.fallbacks.get(task.step)
        if fb_step and task.fallback_of is None:
            fb = self._make_task(plan, fb_step, state.doc, params)
            fb.fallback_of = task.task_id
            self._enqueue(queue, fb)
            return True
        if task.split_id:
            for tid in self.tracker.cancel(task.split_id):
                logger.warning("cancel subtask %s due to parent failure", tid)
        return False

    def _split_id_for(self, task: Task) -> SplitId:
        return task.split_id or f"split@{task.task_id}"

    @staticmethod
    def _scope_of(container: TalismanDocument) -> frozenset[NodeId]:
        return frozenset(container.id2node.keys())

    def _retain_container_blobs(self, doc: TalismanDocument) -> None:
        for node in doc.id2node.values():
            ref = getattr(node, "blob_ref", None)
            if ref is not None:
                self.blobs.retain(ref)

    def _release_consumed(self, result: ProcessorResult | None) -> None:
        if result is None:
            return
        for blob_id in result.consumed_blobs:
            self.blobs.release_by_id(blob_id)
