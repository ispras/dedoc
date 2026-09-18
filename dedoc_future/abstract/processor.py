from abc import ABCMeta, abstractmethod
from typing import Generic, Type, TypeVar

from typing_extensions import Self

from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.enums import ExecMode, Resource

_InputType = TypeVar("_InputType")
_OutputType = TypeVar("_OutputType")
_CheckType = TypeVar("_CheckType")
_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


class AbstractProcessor(Generic[_InputType, _OutputType, _CheckType, _Config, _DeployConfig], metaclass=ABCMeta):
    """
    Abstract processing unit for any stage of the document parsing.
    """

    @property
    def label(self) -> str:
        """
        Textual name of the processor.
        Should be unique for each processor.
        """
        raise NotImplementedError

    @property
    def resource(self) -> Resource:
        """
        Resource that processor needs for a faster work (CPU/GPU).
        """
        raise NotImplementedError

    @property
    def exec_mode(self) -> ExecMode:
        """
        The processor spawns its own OS process or can't do it
        """
        raise NotImplementedError

    @property
    def config_type(self) -> Type[_Config]:
        """
        Configuration type of the processor's process method.
        """
        raise NotImplementedError

    @property
    def deploy_config_type(self) -> Type[_DeployConfig]:
        """
        Configuration type for the processor's initialization.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_config(cls, config: _DeployConfig) -> Self:
        raise NotImplementedError

    @classmethod
    def can_process(cls, data: _CheckType, config: _Config) -> bool:
        """
        Predicate function that returns whether the processor needs to be executed.

        :param data: Data to check.
        :param config: Processing configuration.
        :return: Whether the processor can process the data.
        """
        return True

    @abstractmethod
    def process(self, data: _InputType, config: _Config) -> _OutputType:
        """
        Process the input data and return some result.

        :param data: Data to process.
        :param config: Processing configuration.
        :return: Processing result.
        """
        pass
