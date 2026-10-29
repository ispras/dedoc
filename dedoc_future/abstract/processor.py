# TODO
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractNode, AbstractNodeLink
from typing_extensions import Self

from dedoc_future.abstract.blob_ref import BlobId, BlobRef, NodeId
from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.enums import ExecMode, Resource

_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


@dataclass(frozen=True)
class ContainerSpec:
    nodes: frozenset[type[AbstractNode]] = frozenset()
    include_parents: bool = False
    include_children: bool = False
    links: frozenset[type[AbstractNodeLink]] = frozenset()
    whole_document: bool = False

    def build(self, source: TalismanDocument) -> TalismanDocument:
        if self.whole_document:
            return source

        ids: set[NodeId] = set()
        for node_type in self.nodes:
            ids |= {n.id for n in source.get_nodes(node_type)}

        if self.include_parents:
            for node_id in ids:
                node_parent = source.parent(source.id2node[node_id])
                if node_parent is not None:
                    ids.add(node_parent.id)

        if self.include_children:
            for i in list(ids):
                ids |= {c.id for c in source.child_nodes(source.id2node[i])}

        for link_type in self.links:
            for link in source.node_links.get(link_type, ()):
                if link.source.node.id in ids or link.target.node.id in ids:
                    ids |= {link.source.node.id, link.target.node.id}

        container = source.with_nodes([source.id2node[i] for i in ids])
        container = _get_structure(container, source, ids)
        if self.links:
            kept = [l for l in _all_links(source) if l.source.id in ids and l.target.id in ids]
            container = container.with_node_links(kept)
        return container


@dataclass(frozen=True)
class ResourceProfile:
    resource: Resource = Resource.CPU
    concurrency: ExecMode = ExecMode.THREAD
    batch_size: int | None = None
    gpu_mem_mb: int | None = None
    est_ram_mb: int | None = None


@dataclass(frozen=True)
class ConfigSpec:
    config_type: type[_Config] = ImmutableBaseModel
    deploy_config_type: type[_DeployConfig] = ImmutableBaseModel


@dataclass
class ProcessorResult:
    doc: TalismanDocument
    new_blobs: dict[BlobId, BlobRef] = field(default_factory=dict)
    consumed_blobs: list[BlobId] = field(default_factory=list)


class AbstractProcessor(Generic[_Config, _DeployConfig], metaclass=ABCMeta):
    container_spec: ContainerSpec
    resource_profile: ResourceProfile
    config_spec: ConfigSpec

    @classmethod
    @abstractmethod
    def from_config(cls, config: _DeployConfig) -> Self:
        raise NotImplementedError

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
