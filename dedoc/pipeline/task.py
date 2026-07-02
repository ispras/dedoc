from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional

from dedoc.pipeline.stage import Resource, Scope  # reuse CPU/GPU and PAGE/DOCUMENT


class ExecMode(Enum):
    """
    How a task achieves parallelism on its own - this characterizes the *task*, not the orchestrator.

    - PROCESS: the task spawns its own OS process (e.g. Tesseract OCR, Java tabby); no extra wrapper needed,
      a thread worker is enough because the real work runs in the child process (GIL is released).
    - THREAD: the task cannot spawn its own process; on its own it runs at most in a thread. To get real
      CPU parallelism (past the GIL) the orchestrator hosts such a task inside a persistent CPU process worker.
    """
    PROCESS = "process"
    THREAD = "thread"


class TaskState(Enum):
    """Kept mainly for debugging/observability; the ready/waiting/done sets are the source of truth."""
    WAITING = "waiting"   # some blockers not yet resolved
    READY = "ready"       # all blockers resolved, awaiting a free worker
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"     # produced a warning; still unblocks dependents, which receive this task's input


@dataclass
class TaskSpec:
    """
    Declarative description of one pipeline task type. The orchestrator reads it to decide which worker
    gets the task and how. For scope=PAGE a spec is instantiated into one :class:`Task` per page.

    :ivar name: unique task-type name (used as blocker key)
    :ivar process: the unified entry point ``process(config, input) -> output``
    :ivar resource: CPU or GPU
    :ivar exec_mode: how the task parallelizes itself (see :class:`ExecMode`)
    :ivar batch_size: max batch for GPU specs (>1 groups same-type tasks into one forward); 1 otherwise
    :ivar scope: PAGE (per page) or DOCUMENT (whole document); only PAGE is used for now
    :ivar blockers: names of specs that must finish before this one (edges of the execution graph)
    """
    name: str
    process: Callable[[dict, Any], Any]
    resource: Resource = Resource.CPU
    exec_mode: ExecMode = ExecMode.THREAD
    batch_size: int = 1
    scope: Scope = Scope.PAGE
    blockers: List[str] = field(default_factory=list)
    # optional batched entry point for GPU specs: batch_process([config, ...], [input, ...]) -> [output, ...]
    # (same order/length). If absent, a GPU spec falls back to calling `process` per item (no batching gain).
    batch_process: Optional[Callable[[List[dict], List[Any]], List[Any]]] = None


@dataclass
class Task:
    """
    A concrete unit of work: one :class:`TaskSpec` applied to one page's data.

    :ivar input: set from the (single) blocker's output, or the blocker's own input if the blocker failed
    :ivar config: per-task processing config, e.g. ``{"bbox": ...}`` to process only part of the page
    :ivar priority: static; deeper in the graph => higher, so CPU rushes work toward the GPU tasks
    :ivar output: filled by ``spec.process``; None while pending or on failure
    """
    spec: TaskSpec
    page_number: Optional[int] = None
    input: Any = None
    config: dict = field(default_factory=dict)
    priority: int = 0
    state: TaskState = TaskState.WAITING
    output: Any = None

    @property
    def id(self) -> str:
        return f"{self.spec.name}@p{self.page_number}"
