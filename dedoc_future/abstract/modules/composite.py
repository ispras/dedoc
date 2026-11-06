from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from pydantic import RootModel
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules.abstract import AbstractModule
from dedoc_future.configs.deploy_time import CommonDeployConfig

_Config = TypeVar("_Config", bound=ImmutableBaseModel | RootModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel | RootModel)


@dataclass(frozen=True)
class ModuleSpec:
    module: AbstractModule
    optional: bool


@dataclass(frozen=True)
class ModuleTypeSpec:
    module_type: type[AbstractModule]
    optional: bool


class CompositeModule(AbstractModule[_Config, _DeployConfig], metaclass=ABCMeta):
    def __init__(self) -> None:
        super().__init__()
        self._modules: tuple[ModuleSpec, ...] | None = None

    @classmethod
    def is_available(cls) -> bool:
        for module_type_spec in cls.submodules():
            if module_type_spec.optional:
                continue

            if not module_type_spec.module_type.is_available():
                return False

        return True

    @classmethod
    @abstractmethod
    def submodules(cls) -> tuple[ModuleTypeSpec, ...]:
        ...

    def materialize(self, common_config: CommonDeployConfig) -> Self:
        optional_modules = tuple(module.module_type.name() for module in self.submodules() if module.optional)
        config_all = self.deploy_schema()(root=optional_modules)
        deploy_config: RootModel = common_config.root.get(self.name(), config_all)

        modules: list[ModuleSpec] = []
        for module_type_spec in self.submodules():
            if module_type_spec.optional and module_type_spec.module_type.name() not in deploy_config.root:
                continue
            module = module_type_spec.module_type().materialize(common_config)
            modules.append(ModuleSpec(module=module, optional=module_type_spec.optional))

        if not modules:
            raise ValueError(f"No submodules found for `{self.name()}` module")

        self._modules = tuple(modules)
        return self

    @classmethod
    def deploy_schema(cls) -> type[_DeployConfig]:
        """
        Configure optional modules - use them or not.
        If no configuration was found - use all optional modules.
        """
        optional_modules = [module.module_type.name() for module in cls.submodules() if module.optional]
        options_enum: type[Enum] = Enum("OptionsEnum", {opt: opt for opt in optional_modules})
        deploy_config_type = RootModel[tuple[options_enum, ...]]
        return deploy_config_type

    def runtime_schema(self) -> type[_Config]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        optional_modules = [module.module.name() for module in self._modules if module.optional]
        options_enum: type[Enum] = Enum("OptionsEnum", {opt: opt for opt in optional_modules})
        runtime_config_type = RootModel[tuple[options_enum, ...]]
        return runtime_config_type

    @abstractmethod
    def children(self) -> dict[str, AbstractModule]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        return {spec.module.name(): spec.module for spec in self._modules}

    def resolve_static(self, config: _Config) -> tuple[str, ...]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        result_modules = []
        for module_spec in self._modules:
            if module_spec.optional and module_spec.module.name() not in config.root:
                continue

            resolved = module_spec.module.resolve_static(config)
            if not resolved:
                raise ValueError(f"Could not resolve module `{module_spec.module.name()}`")

            result_modules.extend(resolved)

        return tuple(result_modules)

    def resolve(self, document: TalismanDocument, config: _Config) -> tuple[AbstractModule, ...]:
        raise RuntimeError(f"Composite module `{self.name()}` should be resolved before")
