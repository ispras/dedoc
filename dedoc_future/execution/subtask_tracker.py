import threading
from dataclasses import dataclass, field
from typing import Literal

from dedoc_future.execution.task import SplitId, TaskId, TaskOutput
from dedoc_future.abstract.enums import TaskStatus


@dataclass
class _SplitEntry:
    split_id: SplitId
    total: int
    done: int = 0
    failed: int = 0
    outputs: list[TaskOutput] = field(default_factory=list)
    cancelled: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


class SubtaskTracker:
    def __init__(self, on_failure: Literal["abort_all", "skip_subtask", "fallback"]):
        self._splits: dict[SplitId, _SplitEntry] = {}
        self._lock = threading.RLock()
        self._policy_on_failure = on_failure

    def open(self, split_id: SplitId, n: int) -> None:
        with self._lock:
            if split_id in self._splits:
                raise ValueError(f"split already open: {split_id}")
            if n <= 0:
                self._splits[split_id] = _SplitEntry(split_id, 0)
            else:
                self._splits[split_id] = _SplitEntry(split_id, n)

    def complete(self, split_id: SplitId, out: TaskOutput) -> bool:
        with self._lock:
            entry = self._splits.get(split_id)
            if entry is None:
                raise KeyError(f"split not open: {split_id}")

        with entry.lock:
            if out.status == TaskStatus.ok:
                entry.done += 1
                entry.outputs.append(out)
            elif out.status == TaskStatus.failed:
                entry.failed += 1
                if self._policy_on_failure == "abort_all":
                    entry.cancelled = True
                    return True
            else:
                entry.done += 1
                entry.outputs.append(out)

            finished = entry.cancelled or (entry.done + entry.failed >= entry.total)
            return finished

    def collect(self, split_id: SplitId) -> list[TaskOutput]:
        with self._lock:
            entry = self._splits.pop(split_id)
        return sorted(entry.outputs, key=lambda o: o.task.subtask_id or "")

    def collect_sorted(self, split_id: SplitId, order_map: dict[str, int]) -> list[TaskOutput]:
        with self._lock:
            entry = self._splits.pop(split_id)
        return sorted(entry.outputs, key=lambda o: order_map.get(o.task.subtask_id, 0))

    def cancel(self, split_id: SplitId) -> list[TaskId]:
        with self._lock:
            entry = self._splits.get(split_id)
            if entry is None:
                return []
            entry.cancelled = True
        return [o.task.task_id for o in entry.outputs]

    def has_pending(self) -> bool:
        with self._lock:
            return any(
                not e.cancelled and (e.done + e.failed < e.total)
                for e in self._splits.values()
            )
