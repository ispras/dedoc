from dataclasses import dataclass, field

from tdm import TalismanDocument

from dedoc_future.abstract.modules import AbstractModule, MergeModule
from dedoc_future.errors.config import ConfigError
from dedoc_future.execution.document_state import DocumentState, StepId
from dedoc_future.execution.task import SplitId


@dataclass
class RuntimePlan:
    steps: dict[StepId, AbstractModule]
    edges: dict[StepId, list[StepId]]
    initial_front: list[StepId]
    fallbacks: dict[StepId, StepId] = field(default_factory=dict)

    def successors(self, step: StepId) -> list[StepId]:
        return self.edges.get(step, [])

    def predecessors(self, step: StepId) -> list[StepId]:
        return [s for s, succ in self.edges.items() if step in succ]

    def is_ready(self, step: StepId, state: DocumentState) -> bool:
        return all(self._step_done(p, state) for p in self.predecessors(step))

    def _step_done(self, step: StepId, state: DocumentState) -> bool:
        return step in state.completed_steps

    def merge_for(self, split_id: SplitId) -> StepId:
        for sid, m in self.steps.items():
            if isinstance(m, MergeModule) and m.name == f"merge:{split_id}":
                return sid
        raise ConfigError(f"no MergeModule for split {split_id}")

    def build_container(self, step: StepId, source: TalismanDocument) -> TalismanDocument:
        return self.steps[step].container.build(source)

    def step_for_module(self, module_name: str) -> StepId:
        for sid, m in self.steps.items():
            if m.name == module_name:
                return sid
        raise ConfigError(f"module not in plan: {module_name}")
