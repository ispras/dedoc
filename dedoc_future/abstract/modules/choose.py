from abc import ABCMeta
from enum import Enum
from typing import TypeVar

from pydantic import RootModel

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules.auto import AutoModule

_Config = TypeVar("_Config", bound=ImmutableBaseModel | RootModel)

class ChooseModule(AutoModule, metaclass=ABCMeta):

    def runtime_schema(self) -> type[_Config]:
        if not self._modules:
            raise ValueError(f"Submodules not found for `{self.name()}` module")

        options_enum: type[Enum] = Enum("OptionsEnum", {opt: opt for opt in self._modules})
        runtime_config_type = RootModel[tuple[options_enum, ...]]
        return runtime_config_type
