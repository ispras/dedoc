from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Iterable, Sequence, Type, TypeVar

from pydantic import BaseModel
from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractNode
from typing_extensions import Self

from dedoc_future.abstract.enums import ExecMode, Resource, Scope

_Node = TypeVar("_Node", bound=AbstractNode)
_Config = TypeVar("_Config", bound=BaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=BaseModel)


@dataclass
class ProcessorResult(Generic[_Node]):
    """
    Result returned by `AbstractProcessor`.

    Attributes
    ----------
    nodes:
        existing nodes in the document that were changed
    structure:
        new nodes (along with their structure) that need to be added to the document
    """
    nodes: Iterable[_Node]
    structure: dict[AbstractNode, Iterable[AbstractNode]]


class AbstractProcessor(Generic[_Node, _Config, _DeployConfig], metaclass=ABCMeta):
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
    def scope(self) -> Scope:
        """
        Granularity at which the processor operates (specific node or the whole document).
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
    def node_type(self) -> Type[_Node]:
        """
        Type of document nodes that the processor needs.
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

    @property
    def predicate(self) -> Callable[[TalismanDocument, _Node, _Config], bool]:
        """
        Predicate function that returns whether the processor needs to be executed.
        """
        return lambda document, node, config: True

    @abstractmethod
    def process(self, document: TalismanDocument, nodes: Sequence[_Node], config: _Config) -> ProcessorResult[_Node]:
        """
        Process the input document and return an enriched document.

        :param document: Document to process.
        :param nodes: Nodes to process (only these nodes will be changed). The nodes should belong to the given document.
        :param config: Processing configuration.
        :return: Changed input nodes and new nodes with structure.
        """
        pass
