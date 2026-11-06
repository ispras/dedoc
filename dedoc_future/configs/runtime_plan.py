from __future__ import annotations

import logging
from dataclasses import dataclass

import networkx as nx
from tdm import TalismanDocument

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules.abstract import AbstractModule
from dedoc_future.configs.runtime import RuntimeConfig
from dedoc_future.execution.document_state import StepId

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedStep:
    module: AbstractModule
    step_id: StepId
    params: ImmutableBaseModel
    dependencies: frozenset[str]


class RuntimePlan:

    def __init__(self, graph: nx.DiGraph, modules: dict[str, AbstractModule], runtime_config: RuntimeConfig):
        self._graph = graph
        self._modules = modules
        self._config = runtime_config
        self._completed: set[StepId] = set()
        self._failed: set[StepId] = set()
        self._in_progress: set[StepId] = set()

    def ready_steps(self, document: TalismanDocument) -> list[ResolvedStep]:
        result: list[ResolvedStep] = []

        for name, module in self._modules.items():
            if self._is_done(name) or not self._blockers_done(module):
                continue

            chain = self._resolve(module, document)
            if not chain:
                continue

            prev_step: str | None = None
            for i, resolved_module in enumerate(chain):
                step_id = f"{name}::{i}"
                if step_id in self._completed:
                    prev_step = step_id
                    continue
                result.append(ResolvedStep(
                    module=resolved_module,
                    step_id=step_id,
                    params=self._config.get_for(self._modules[resolved_module.name()]),
                    dependencies=self._dependencies(name, prev_step),
                ))
                prev_step = step_id

        return result

    def _resolve(self, module: AbstractModule, document: TalismanDocument) -> tuple[AbstractModule, ...]:
        return module.resolve(document, self._config.get_for(module))

    def _blockers_done(self, module: AbstractModule) -> bool:
        return all(b in self._completed for b in module.blockers)

    def _dependencies(self, name: str, prev_step: str | None) -> frozenset[str]:
        deps = {f"{p}::last" for p in self._graph.predecessors(name) if p in self._completed}
        if prev_step is not None:
            deps.add(prev_step)
        return frozenset(deps)

    def _is_done(self, name: str) -> bool:
        return name in self._completed or name in self._failed

    def mark_started(self, name: str, step_id: str) -> None:
        self._in_progress.add(step_id)

    def mark_completed(self, name: str, step_id: str, chain_len: int) -> None:
        self._in_progress.discard(step_id)
        self._completed.add(step_id)
        if step_id == f"{name}::{chain_len - 1}":
            self._completed.add(name)

    def mark_failed(self, name: str, step_id: str) -> None:
        self._in_progress.discard(step_id)
        self._failed.add(step_id)
        self._failed.add(name)

    @property
    def is_finished(self) -> bool:
        return all(self._is_done(n) for n in self._modules)

    @property
    def has_failed(self) -> bool:
        return bool(self._failed)

    def pending_blocked(self) -> list[str]:
        return [n for n, m in self._modules.items() if not self._is_done(n) and not self._blockers_done(m)]
