from __future__ import annotations

import logging

from networkx import DiGraph, is_directed_acyclic_graph

from dedoc_future.abstract.modules import AbstractModule
from dedoc_future.configs.deploy_time import CommonDeployConfig
from dedoc_future.configs.runtime import RuntimeConfig
from dedoc_future.configs.runtime_plan import RuntimePlan
from dedoc_future.errors.config import ConfigError, UnavailableModuleError
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

    def bind(self, runtime_config: RuntimeConfig) -> RuntimePlan:
        # resolve enums and optional modules
        active_modules = set()
        for module in self._modules.values():
            module_config = runtime_config.get_for(module)
            active_modules.update(module.resolve_static(module_config))

        subgraph = self._graph.subgraph(active_modules).copy()
        if not is_directed_acyclic_graph(subgraph):
            raise ConfigError("Module graph contains a cycle")

        return RuntimePlan(
            graph=subgraph,
            modules={module_name: module for module_name, module in self._modules.items() if module_name in active_modules},
            runtime_config=runtime_config,
        )
