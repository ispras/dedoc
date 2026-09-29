from dataclasses import replace
from typing import Sequence, Type

import magic
import puremagic
from typing_extensions import Self

from dedoc.extensions import mime2extension
from dedoc.utils.utils import splitext_
from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.datamodel.nodes.file import FileNode


class ContentMimeDetector(AbstractNodeProcessor[FileNode, ImmutableBaseModel, ImmutableBaseModel]):
    @property
    def label(self) -> str:
        return "content_mime_detector"

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
            mime = magic.from_file(node.content, mime=True)

            if mime == "application/octet-stream":  # for files with mime in {"image/x-sun-raster", "image/x-ms-bmp"}
                try:
                    mime = puremagic.from_file(node.content, mime=True)
                except puremagic.main.PureError:
                    pass

            extension = mime2extension.get(mime, splitext_(node.content)[1])
            metadata = replace(node.metadata, mime=mime, extension=extension)
            result_nodes.append(replace(node, metadata=metadata))

        return NodeProcessorResult(changed_nodes=result_nodes)
