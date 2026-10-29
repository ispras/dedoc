from dataclasses import dataclass, field
from enum import Enum

from tdm import TalismanDocument

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.blob_ref import NodeId
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.execution.document_state import StepId

TaskId = str
SubtaskId = str
SplitId = str


class TaskStatus(str, Enum):
    ok = "ok"
    failed = "failed"
    fallback = "fallback"


@dataclass(frozen=True)
class SubtaskSpec:
    module_name: str
    scope: frozenset[NodeId]
    order: int


@dataclass(frozen=True)
class Task:
    task_id: TaskId
    step: StepId
    module_name: str
    container: TalismanDocument
    params: ImmutableBaseModel
    priority: int
    split_id: SplitId | None = None
    subtask_id: SubtaskId | None = None


@dataclass
class TaskOutput:
    task: Task
    result: ProcessorResult | None
    status: TaskStatus
    subtasks: list[SubtaskSpec] = field(default_factory=list)
