from typing import Sequence, Type

from tdm.abstract.datamodel import AbstractNode
from typing_extensions import Self

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.configs.base import BaseProcessorConfig
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.helpers.formats import format_suits


class DocxProcessor(AbstractNodeProcessor[FileNode, ImmutableBaseModel, ImmutableBaseModel]):
    @property
    def label(self) -> str:
        return "docx"

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
    def config_type(self) -> Type[BaseProcessorConfig]:
        return BaseProcessorConfig

    @property
    def deploy_config_type(self) -> Type[ImmutableBaseModel]:
        return ImmutableBaseModel

    @classmethod
    def from_config(cls, config: ImmutableBaseModel) -> Self:
        return cls()

    @classmethod
    def can_process(cls, data: AbstractNode, config: ImmutableBaseModel) -> bool:
        return super().can_process(data, config) and format_suits(data, recognized_extensions.docx_like_format, recognized_mimes.docx_like_format)

    def process(self, data: Sequence[FileNode], config: ImmutableBaseModel) -> NodeProcessorResult[FileNode]:
        ...
