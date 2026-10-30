from __future__ import annotations

import logging
from collections import defaultdict, deque

from networkx import DiGraph, is_directed_acyclic_graph
from tdm import TalismanDocument

from dedoc_future.abstract.modules import AbstractModule, AutoModule, ChooseModule
from dedoc_future.configs.deploy_time import CommonDeployConfig
from dedoc_future.configs.runtime import RuntimeConfig
from dedoc_future.configs.runtime_plan import RuntimePlan
from dedoc_future.errors.config import ConfigError, RuntimeConfigError, UnavailableModuleError
from dedoc_future.execution.document_state import StepId
from dedoc_future.modules.registry import ModuleRegistry

logger = logging.getLogger(__name__)


class SystemConfig:

    def __init__(
            self,
            registry: ModuleRegistry,
            root_module: AbstractModule,
            modules: dict[str, AbstractModule],
            strict: bool = False
    ) -> None:
        self._registry = registry
        self._root_module = root_module
        self._modules = modules
        self._strict = strict
        self._graph = self._build_graph()

    def _build_graph(self) -> DiGraph:
        graph = DiGraph()
        for m in self._modules.values():
            for b in m.blockers:
                if b not in self._modules:
                    raise ConfigError(f"{m.name()}: blocker {b} not included in config")
                graph.add_edge(b, m.name())

        if not is_directed_acyclic_graph(graph):
            raise ConfigError("Modules graph has cycles")

        return graph

    def get_module(self, name: str) -> AbstractModule:
        return self._modules[name]

    @classmethod
    def from_declarative_config(
            cls,
            deploy_config: CommonDeployConfig,
            registry: ModuleRegistry,
            *,
            strict: bool = False
    ) -> SystemConfig:
        available_modules = registry.available_modules
        root_name = deploy_config.root_module
        if deploy_config.root_module not in available_modules:
            raise UnavailableModuleError(f"Root module unavailable: {root_name}")

        names = list(deploy_config.root) + [root_name]
        modules: dict[str, AbstractModule] = {}

        while len(names) > 0:
            name = names.pop()
            if name not in available_modules:
                if strict:
                    raise UnavailableModuleError(f"Module unavailable: {name}")
                logger.warning(f"Skip unavailable module: {name}")
                continue

            if name in modules:
                continue

            module = registry.get(name)().materialize(deploy_config)
            modules[name] = module
            names.extend(module.children())

        return cls(registry=registry, root_module=modules[root_name], modules=modules, strict=strict)

    def bind(self, runtime_config: RuntimeConfig, document: TalismanDocument) -> RuntimePlan:
        modules_to_resolve = deque([self._root_module])
        resolved_modules = []

        while len(modules_to_resolve) > 0:
            module = modules_to_resolve.popleft()
            module_config = runtime_config.get_for(module)
            submodules = module.resolve(document, module_config)
            if not submodules:
                resolved_modules.append(module)
            else:
                modules_to_resolve.extend(submodules)

        resolved: dict[StepId, AbstractModule] = {}
        fallbacks: dict[StepId, StepId] = {}

        self._resolve(self.root, "root", runtime_config, document)

        preds = self._preds_from_resolved(resolved)
        initial = [s for s in resolved if not preds[s]]

        return RuntimePlan(
            steps=resolved,
            edges=self._edges_from_resolved(resolved),
            initial_front=initial,
            fallbacks=fallbacks,
        )

    def _resolve(self, m: AbstractModule, ctx: str, runtime_config: RuntimeConfig, document: TalismanDocument) -> list[StepId]:
        steps: list[StepId] = []

        if isinstance(m, ChooseModule):
            key = getattr(runtime_config.get_for(m.name, self), m.param_name)
            if key is None:
                raise RuntimeConfigError(f"{ctx}: runtime param '{m.name}.{m.param_name}' not set")
            if key not in m.options:
                raise RuntimeConfigError(f"{ctx}: value '{key}' not among options {list(m.options)}")
            steps += self._resolve(m.options[key], f"{ctx}/{m.name}={key}", runtime_config, document)

        elif isinstance(m, AutoModule):
            ids = [resolve(o, f"{ctx}/{m.name}") for o in m.options]
            for i, chain in enumerate(ids):
                steps += chain
                if i > 0:  # fallback: primary -> option_i
                    fallbacks[ids[0][0]] = chain[0]
        else:
            sid: StepId = f"{ctx}/{m.name}"
            resolved[sid] = m
            steps.append(sid)
            for ch in m.children():
                steps += resolve(ch, sid)

        return steps

    def _preds_from_resolved(self, resolved: dict[StepId, AbstractModule]) -> dict[StepId, set[StepId]]:
        preds = {s: set() for s in resolved}
        for s, m in resolved.items():
            for b in m.blockers:
                for t, tm in resolved.items():
                    if tm.name == b:
                        preds[s].add(t)
        return preds

    def _edges_from_resolved(self, resolved: dict[StepId, AbstractModule]) -> dict[StepId, list[StepId]]:
        edges: dict[StepId, list[StepId]] = defaultdict(list)
        for s, m in resolved.items():
            for b in m.blockers:
                for t, tm in resolved.items():
                    if tm.name == b:
                        edges[t].append(s)
        return dict(edges)
