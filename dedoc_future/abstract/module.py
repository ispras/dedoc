# TODO class variables instead of attributes; modules implementation
from __future__ import annotations
from dataclasses import dataclass

from dedoc_future.abstract import AbstractProcessor, ImmutableBaseModel
from dedoc_future.abstract.processor import ContainerSpec


@dataclass(frozen=True)
class AbstractModule:
    name: str
    description: str
    blockers: tuple[str, ...]
    container: ContainerSpec

    @classmethod
    def is_available(cls) -> bool:
        raise NotImplementedError

    @classmethod
    def deploy_schema(cls) -> type[ImmutableBaseModel]:
        raise NotImplementedError

    @classmethod
    def runtime_schema(cls) -> type[ImmutableBaseModel]:
        raise NotImplementedError

    @classmethod
    def from_config(cls, config: ImmutableBaseModel) -> AbstractModule:
        raise NotImplementedError

    def children(self) -> tuple[AbstractModule, ...]:
        raise NotImplementedError


class SimpleModule(AbstractModule):
    deploy_config: ImmutableBaseModel

    @classmethod
    def processor_type(cls) -> type[AbstractProcessor]:
        raise NotImplementedError

    @classmethod
    def deploy_schema(cls) -> type[ImmutableBaseModel]:
        return cls.processor_type().config_spec.deploy_config_type

    @classmethod
    def runtime_schema(cls) -> type[ImmutableBaseModel]:
        return cls.processor_type().config_spec.config_type


class CompositeModule(AbstractModule):
    children: tuple[AbstractModule, ...]
    optional: bool = False


class AutoModule(AbstractModule):
    options: list[AbstractModule]


class ChooseModule(AbstractModule):
    options: dict[str, AbstractModule]
    param_name: str


class SplitModule(AbstractModule):
    processor_type: type[AbstractProcessor]
    subtask_module: AbstractModule


class MergeModule(AbstractModule):
    processor_type: type[AbstractProcessor]
