from collections import defaultdict
from typing import Callable, Sequence, Type

import cv2
from pdf2image.pdf2image import _page_count
from pydantic import BaseModel
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.metadata.page import PageMetadata
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.helpers.formats import format_suits


class PagesCreator(AbstractProcessor[FileNode, PdfBaseConfig, BaseModel]):
    """
    Create PDF/image page nodes for further enriching.
    """

    @property
    def label(self) -> str:
        return "pages_creator"

    @property
    def scope(self) -> Scope:
        return Scope.NODE

    @property
    def resource(self) -> Resource:
        return Resource.CPU

    @property
    def exec_mode(self) -> ExecMode:
        return ExecMode.PROCESS  # because of `pdf2image._page_count` by poppler

    @property
    def node_type(self) -> Type[FileNode]:
        return FileNode

    @property
    def config_type(self) -> Type[PdfBaseConfig]:
        return PdfBaseConfig

    @property
    def deploy_config_type(self) -> Type[BaseModel]:
        return BaseModel

    @classmethod
    def from_config(cls, config: BaseModel) -> Self:
        return cls()

    @property
    def predicate(self) -> Callable[[TalismanDocument, FileNode, PdfBaseConfig], bool]:
        return lambda document, node, confing: bool(node.metadata and node.metadata.need_parse)  # TODO maybe check format

    def process(self, document: TalismanDocument, nodes: Sequence[FileNode], config: PdfBaseConfig) -> ProcessorResult[FileNode]:
        page_nodes = defaultdict(list)
        for node in nodes:
            if format_suits(node, recognized_extensions.image_like_format, recognized_mimes.image_like_format):
                image = cv2.imread(node.content)
                metadata = PageMetadata(number=0, file_ref=node)
                page_nodes[node].append(PageNodeWrapper.wrap(PageNode(metadata=metadata)).set_orig_image(image))
            else:  # PDF
                pages_count = _page_count(node.content)  # TODO look for another stable way to gen number of pages
                for page_number in range(config.start_page, min(config.end_page, pages_count)):
                    metadata = PageMetadata(number=page_number, file_ref=node)
                    page_nodes[node].append(PageNode(metadata=metadata))

        return ProcessorResult(nodes=nodes, structure=page_nodes)
