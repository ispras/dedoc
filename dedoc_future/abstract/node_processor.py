from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Iterable, Sequence, Type, TypeVar

from tdm.abstract.datamodel import AbstractNode

from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.processor import AbstractProcessor

_Node = TypeVar("_Node", bound=AbstractNode)
_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


@dataclass
class NodeProcessorResult(Generic[_Node]):
    """
    Result returned by `AbstractNodeProcessor`.

    Attributes
    ----------
    changed_nodes:
        input nodes that were changed
    new_nodes:
        new nodes (along with their structure)
    delete_nodes:
        input nodes that need to be deleted
    """
    changed_nodes: Sequence[_Node] = field(default_factory=list)
    new_nodes: dict[AbstractNode, Iterable[AbstractNode]] = field(default_factory=dict)
    delete_nodes: Sequence[_Node] = field(default_factory=list)


class AbstractNodeProcessor(AbstractProcessor[Sequence[_Node], NodeProcessorResult[_Node], AbstractNode, _Config, _DeployConfig], metaclass=ABCMeta):
    @classmethod
    def node_type(cls) -> Type[_Node]:
        raise NotImplementedError

    @classmethod
    def can_process(cls, data: AbstractNode, config: _Config) -> bool:
        return isinstance(data, cls.node_type())

    @abstractmethod
    def process(self, data: Sequence[_Node], config: _Config) -> NodeProcessorResult[_Node]:
        """
        Process input nodes and return the result with changed/new/delete nodes.

        :param data: Several nodes of the same type to process.
        :param config: Processing configuration.
        :return: Processing result.
        """
        pass
