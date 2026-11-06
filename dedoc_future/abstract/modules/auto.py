from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import TypeVar

from pydantic import RootModel
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules.abstract import AbstractModule
from dedoc_future.configs.deploy_time import CommonDeployConfig

_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel | RootModel)


class AutoModule(AbstractModule[_Config, _DeployConfig], metaclass=ABCMeta):

    def __init__(self) -> None:
        super().__init__()
        self._modules: dict[str, AbstractModule] | None = None

    @classmethod
    def is_available(cls) -> bool:
        for module_type in cls.options().values():
            if module_type.is_available():
                return True

        return False

    @classmethod
    @abstractmethod
    def options(cls) -> dict[str, type[AbstractModule]]:
        ...

    def materialize(self, common_config: CommonDeployConfig) -> Self:
        config_all = self.deploy_schema()(root=tuple(self.options()))
        deploy_config: RootModel = common_config.root.get(self.name(), config_all)
        self._modules = {}
        for option in deploy_config.root:
            module_type = self.options().get(option)
            if module_type is None:
                raise ValueError(f"Invalid option for `{self.name()}` module: {option}")

            self._modules[option] = module_type().materialize(common_config)

        if not self._modules:
            raise ValueError(f"No options found for `{self.name()}` module")
        return self

    @classmethod
    def deploy_schema(cls) -> type[_DeployConfig]:
        options_enum: type[Enum] = Enum("OptionsEnum", {opt: opt for opt in cls.options()})
        deploy_config_type = RootModel[tuple[options_enum, ...]]
        return deploy_config_type

    def runtime_schema(self) -> type[_Config]:
        return ImmutableBaseModel

    @abstractmethod
    def children(self) -> dict[str, AbstractModule]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        return self._modules

    def resolve_static(self, config: _Config) -> tuple[str, ...]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        result = [self.name()]
        for module in self._modules.values():
            result.extend(module.resolve_static(config))

        return tuple(result)

    def resolve(self, document: TalismanDocument, config: _Config) -> tuple[AbstractModule, ...]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        for module in self._modules.values():
            resolved = module.resolve(document, config)
            if resolved:
                # choose the first suitable submodule
                return resolved

        raise ValueError(f"No option was found for `{self.name()}` module")
