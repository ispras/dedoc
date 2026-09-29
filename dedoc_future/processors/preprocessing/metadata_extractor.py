import mimetypes
import os
from dataclasses import replace
from pathlib import Path
from typing import Sequence, Type

from typing_extensions import Self

from dedoc.utils.utils import splitext_
from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.datamodel.nodes.file import FileNode


class MetadataExtractor(AbstractNodeProcessor[FileNode, ImmutableBaseModel, ImmutableBaseModel]):
    @property
    def label(self) -> str:
        return "metadata_extractor"

    @property
    def resource(self) -> Resource:
        return Resource.CPU

    @property
    def exec_mode(self) -> ExecMode:
        return ExecMode.THREAD

    @classmethod
    def node_type(cls) -> Type[FileNode]:
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

    def process(self, data: Sequence[FileNode], config: ImmutableBaseModel) -> NodeProcessorResult[FileNode]:
        result_nodes = []
        for node in data:
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

        return NodeProcessorResult(changed_nodes=result_nodes)
