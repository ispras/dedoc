from dataclasses import replace
from typing import Sequence, Type

import magic
import puremagic
from pydantic import BaseModel
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc.extensions import mime2extension
from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.datamodel.nodes.file import FileNode


class ContentMimeDetector(AbstractProcessor[FileNode, BaseModel, BaseModel]):
    @property
    def label(self) -> str:
        return "content_mime_detector"

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
    def config_type(self) -> Type[BaseModel]:
        return BaseModel

    @property
    def deploy_config_type(self) -> Type[BaseModel]:
        return BaseModel

    @classmethod
    def from_config(cls, config: BaseModel) -> Self:
        return cls()

    def process(self, document: TalismanDocument, nodes: Sequence[FileNode], config: BaseModel) -> ProcessorResult[FileNode]:
        result_nodes = []
        for node in nodes:
            mime = magic.from_file(node.content, mime=True)

            if mime == "application/octet-stream":  # for files with mime in {"image/x-sun-raster", "image/x-ms-bmp"}
                try:
                    mime = puremagic.from_file(node.content, mime=True)
                except puremagic.main.PureError:
                    pass

            extension = mime2extension.get(mime, "")
            metadata = replace(node.metadata, mime=mime, extension=extension)
            result_nodes.append(replace(node, metadata=metadata))

        return ProcessorResult(nodes=result_nodes, structure={})
