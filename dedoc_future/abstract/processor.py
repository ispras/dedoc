from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract.blob_ref import BlobId, BlobRef
from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.container_spec import ContainerSpec
from dedoc_future.abstract.enums import ExecMode, Resource

_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


@dataclass(frozen=True)
class ResourceProfile:
    resource: Resource = Resource.CPU
    concurrency: ExecMode = ExecMode.THREAD
    batch_size: int | None = None
    gpu_mem_mb: int | None = None
    est_ram_mb: int | None = None


@dataclass(frozen=True)
class ConfigSpec:
    runtime_schema: type[_Config] = ImmutableBaseModel
    deploy_schema: type[_DeployConfig] = ImmutableBaseModel


@dataclass
class ProcessorResult:
    doc: TalismanDocument
    new_blobs: dict[BlobId, BlobRef] = field(default_factory=dict)
    consumed_blobs: list[BlobId] = field(default_factory=list)


class AbstractProcessor(Generic[_Config, _DeployConfig], metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def container_spec(cls) -> ContainerSpec:
        ...

    @classmethod
    @abstractmethod
    def resource_profile(cls) -> ResourceProfile:
        ...

    @classmethod
    @abstractmethod
    def config_spec(cls) -> ConfigSpec:
        ...

    @classmethod
    @abstractmethod
    def from_config(cls, config: _DeployConfig) -> Self:
        ...

    @classmethod
    def can_process(cls, data: TalismanDocument, config: _Config) -> bool:
        """
        Predicate function that returns whether the processor needs to be executed.

        :param data: Data to check.
        :param config: Processing configuration.
        :return: Whether the processor can process the data.
        """
        return True

    @abstractmethod
    def process(self, data: TalismanDocument, config: _Config) -> ProcessorResult:
        """
        Process the input data and return some result.

        :param data: Data to process.
        :param config: Processing configuration.
        :return: Processing result.
        """
        pass
