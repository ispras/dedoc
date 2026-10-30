from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.configs.deploy_time import CommonDeployConfig

_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


class AbstractModule(Generic[_Config, _DeployConfig], metaclass=ABCMeta):

    def __init__(self) -> None:
        self._blockers: tuple[str, ...] | None = None

    def set_blockers(self, blockers: tuple[str, ...]) -> None:
        self._blockers = blockers

    @property
    def blockers(self) -> tuple[str, ...]:
        if self._blockers is None:
            raise AttributeError("Attribute `blockers` has not been set")
        return self._blockers

    @abstractmethod
    def materialize(self, common_config: CommonDeployConfig) -> Self:
        ...

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        ...

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def deploy_schema(cls) -> type[_DeployConfig]:
        ...

    @abstractmethod
    def runtime_schema(self) -> type[_Config]:
        ...

    @abstractmethod
    def children(self) -> dict[str, AbstractModule]:
        ...

    @abstractmethod
    def resolve(self, document: TalismanDocument, config: _Config) -> tuple[AbstractModule, ...]:
        ...
