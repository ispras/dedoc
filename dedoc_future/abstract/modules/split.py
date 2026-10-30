from abc import ABCMeta
from typing import Self

from dedoc_future.abstract import ImmutableBaseModel
from dedoc_future.abstract.modules.abstract import AbstractModule
from dedoc_future.configs.deploy_time import CommonDeployConfig


class SplitModule(AbstractModule, metaclass=ABCMeta):
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
