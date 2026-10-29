from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass

from tdm import TalismanDocument

from dedoc_future.abstract.module import AbstractModule, AutoModule, ChooseModule
from dedoc_future.configs.runtime import RuntimeConfig
from dedoc_future.errors.config import ConfigError, RuntimeConfigError, UnavailableModuleError
from dedoc_future.execution.document_state import StepId
from dedoc_future.modules.registry import ModuleRegistry
from dedoc_future.configs.runtime_plan import RuntimePlan

logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    registry: ModuleRegistry
    root: AbstractModule
    modules: dict[str, AbstractModule]
    graph: dict[str, list[str]]
    strict: bool = False

    def get_module(self, name: str) -> AbstractModule:
        ...

    @classmethod
    def from_declarative(
            cls,
            deploy_config: dict,
            registry: ModuleRegistry,
            *,
            strict: bool = False
    ) -> SystemConfig:
        available_modules = registry.available_modules
        root_name = deploy_config["root"]
        if root_name not in available_modules:
            raise UnavailableModuleError(f"Root module unavailable: {root_name}")

        names = deploy_config["modules"] + [root_name]
        module_types: list[type[AbstractModule]] = []

        for name in names:
            if name not in available_modules:
                if strict:
                    raise UnavailableModuleError(f"Module unavailable: {name}")
                logger.warning(f"Skip unavailable module: {name}")
                continue
            module_types.append(registry.get(name))

        deploy = deploy_config.get("deploy", {})
        modules = {}
        for module_type in module_types:
            deploy_config = deploy.get(module_type.name, {})
            schema = module_type.deploy_schema()
            modules[module_type.name] = module_type.from_config(schema.model_validate(deploy_config))

        cfg = cls(registry=registry, root=modules[root_name], modules=modules, graph={}, strict=strict)
        cfg._build_graph()
        cfg.validate()
        return cfg

    def _build_graph(self) -> None:
        edges: dict[str, list[str]] = defaultdict(list)
        for m in self.modules.values():
            for b in m.blockers:
                if b not in self.modules:
                    raise ConfigError(f"{m.name}: blocker {b} not included in config")
                edges[b].append(m.name)

        self.graph = dict(edges)

    def validate(self) -> None:
        # TODO use some tool for this
        WHITE, GREY, BLACK = 0, 1, 2
        color = {n: WHITE for n in self.modules}

        def dfs(n: str):
            color[n] = GREY
            for s in self.graph.get(n, []):
                if color[s] == GREY:
                    raise ConfigError(f"cycle detected involving {n} -> {s}")
                if color[s] == WHITE:
                    dfs(s)
            color[n] = BLACK

        for n in self.modules:
            if color[n] == WHITE:
                dfs(n)

    def bind(self, runtime_config: RuntimeConfig, document: TalismanDocument) -> RuntimePlan:
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
