from abc import ABCMeta, abstractmethod
from typing import TypeVar

from typing_extensions import Self

from dedoc_future.abstract import AbstractProcessor, ImmutableBaseModel
from dedoc_future.configs.deploy_time import CommonDeployConfig
from dedoc_future.abstract.modules.abstract import AbstractModule

_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


class SimpleModule(AbstractModule[_Config, _DeployConfig], metaclass=ABCMeta):

    def __init__(self) -> None:
        super().__init__()
        self._processor: AbstractProcessor | None = None

    def materialize(self, common_config: CommonDeployConfig) -> Self:
        deploy_config = common_config.root.get(self.name(), self.deploy_schema()())
        self._processor = self.processor_type().from_config(deploy_config)
        return self

    @classmethod
    @abstractmethod
    def processor_type(cls) -> type[AbstractProcessor]:
        ...

    @classmethod
    def deploy_schema(cls) -> type[_DeployConfig]:
        return cls.processor_type().config_spec().deploy_schema

    def runtime_schema(self) -> type[_Config]:
        return self.processor_type().config_spec().runtime_schema

    def children(self) -> dict[str, AbstractModule]:
        return {}
