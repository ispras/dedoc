from typing import Callable, Sequence, Type

from pydantic import BaseModel
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.configs.base import BaseProcessorConfig
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.helpers.formats import format_suits


class DocxProcessor(AbstractProcessor[FileNode, BaseProcessorConfig, BaseModel]):
    @property
    def label(self) -> str:
        return "docx"

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
    def config_type(self) -> Type[BaseProcessorConfig]:
        return BaseProcessorConfig

    @property
    def deploy_config_type(self) -> Type[BaseModel]:
        return BaseModel

    @classmethod
    def from_config(cls, config: BaseModel) -> Self:
        return cls()

    @property
    def predicate(self) -> Callable[[TalismanDocument, FileNode, BaseProcessorConfig], bool]:
        return lambda document, node, config: format_suits(node, recognized_extensions.docx_like_format, recognized_mimes.docx_like_format)

    def process(self, document: TalismanDocument, nodes: Sequence[FileNode], config: BaseProcessorConfig) -> ProcessorResult[FileNode]:
        ...
