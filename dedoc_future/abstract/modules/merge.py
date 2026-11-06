from abc import ABCMeta
from typing import Self

from tdm import TalismanDocument

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules.abstract import AbstractModule
from dedoc_future.configs.deploy_time import CommonDeployConfig


class MergeModule(AbstractModule, metaclass=ABCMeta):
    def materialize(self, common_config: CommonDeployConfig) -> Self:
        return self

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def deploy_schema(cls) -> type[ImmutableBaseModel]:
        return ImmutableBaseModel

    def runtime_schema(self) -> type[ImmutableBaseModel]:
        return ImmutableBaseModel

    def children(self) -> dict[str, AbstractModule]:
        return {}

    def resolve_static(self, config: ImmutableBaseModel) -> tuple[str, ...]:
        return (self.name(),)

    def resolve(self, document: TalismanDocument, config: ImmutableBaseModel) -> tuple[AbstractModule, ...]:
        return (self,)
