import mimetypes
import os
from dataclasses import replace
from pathlib import Path
from typing import Sequence, Type

from tdm import TalismanDocument
from typing_extensions import Self

from dedoc.utils.utils import splitext_
from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.datamodel.nodes.file import FileNode


class MetadataExtractor(AbstractProcessor[FileNode, ImmutableBaseModel, ImmutableBaseModel]):
    @property
    def label(self) -> str:
        return "metadata_extractor"

    @property
    def scope(self) -> Scope:
        return Scope.NODE

    @property
    def resource(self) -> Resource:
        return Resource.CPU

    @property
    def exec_mode(self) -> ExecMode:
        return ExecMode.THREAD

    @property
    def node_type(self) -> Type[FileNode]:
        return FileNode

    @property
    def config_type(self) -> Type[ImmutableBaseModel]:
        return ImmutableBaseModel

    @property
    def deploy_config_type(self) -> Type[ImmutableBaseModel]:
        return ImmutableBaseModel

    @classmethod
    def from_config(cls, config: ImmutableBaseModel) -> Self:
        return cls()

    def process(self, document: TalismanDocument, nodes: Sequence[FileNode], config: ImmutableBaseModel) -> ProcessorResult[FileNode]:
        result_nodes = []
        for node in nodes:
            (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(node.content)
            metadata_dict = {
                "mime": mimetypes.guess_type(node.content)[0] or "application/octet-stream",
                "name": Path(node.content).name,
                "extension": splitext_(node.content)[1],
                "size": size,
                "modified_time": mtime,
                "created_time": ctime,
                "access_time": atime
            }

            metadata = replace(node.metadata, **metadata_dict)
            result_nodes.append(replace(node, metadata=metadata))

        return ProcessorResult(nodes=result_nodes, structure={})
