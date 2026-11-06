from abc import ABCMeta
from enum import Enum
from typing import TypeVar

from pydantic import RootModel, create_model
from tdm import TalismanDocument

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules import AbstractModule
from dedoc_future.abstract.modules.auto import AutoModule

_Config = TypeVar("_Config", bound=ImmutableBaseModel)

class ChooseModule(AutoModule, metaclass=ABCMeta):
    """
    TODO: default value of enum
    """

    def runtime_schema(self) -> type[_Config]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        options_enum: type[Enum] = Enum("OptionsEnum", {opt: opt for opt in self._modules})

        class ChooseModuleConfig(ImmutableBaseModel):
            type: options_enum

        return ChooseModuleConfig

    def resolve_static(self, config: _Config) -> tuple[str, ...]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        module_name = config.type.value
        module = self._modules.get(module_name)

        if module is None:
            raise ValueError(f"Config option `{module_name}` not found for `{self.name()}` module")

        return module.resolve_static(config)

    def resolve(self, document: TalismanDocument, config: _Config) -> tuple[AbstractModule, ...]:
        raise RuntimeError(f"Choose module `{self.name()}` should be resolved before")
