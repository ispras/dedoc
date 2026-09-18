from collections import defaultdict
from typing import Sequence, Type

import cv2
import numpy as np
from pdf2image.pdf2image import convert_from_path
from tdm.abstract.datamodel import AbstractNode
from typing_extensions import Self

from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper


class PopplerRender(AbstractNodeProcessor[PageNode, PdfBaseConfig, ImmutableBaseModel]):
    """
    Render images for pdf pages using poppler.
    """

    @property
    def label(self) -> str:
        return "poppler_render"

    @property
    def resource(self) -> Resource:
        return Resource.CPU

    @property
    def exec_mode(self) -> ExecMode:
        return ExecMode.PROCESS  # because of using poppler in pdf2image

    @classmethod
    def node_type(cls) -> Type[PageNode]:
        return PageNode

    @property
    def config_type(self) -> Type[PdfBaseConfig]:
        return PdfBaseConfig

    @property
    def deploy_config_type(self) -> Type[ImmutableBaseModel]:
        return ImmutableBaseModel

    @classmethod
    def from_config(cls, config: ImmutableBaseModel) -> Self:
        return cls()

    @classmethod
    def can_process(cls, data: AbstractNode, config: PdfBaseConfig) -> bool:
        return super().can_process(data, config) and PageNodeWrapper.wrap(data).orig_image is None

    def process(self, data: Sequence[PageNode], config: PdfBaseConfig) -> NodeProcessorResult[PageNode]:
        file2pages = defaultdict(list)
        for node in data:
            file2pages[node.metadata.file_ref].append(node)

        result_nodes = []
        for file_node, page_nodes in file2pages.items():
            page_nodes = sorted(page_nodes, key=lambda x: x.metadata.number)
            start_page = page_nodes[0].metadata.number
            images = convert_from_path(file_node.content, first_page=start_page + 1, last_page=page_nodes[-1].metadata.number + 1)
            for page_node in page_nodes:
                page_image = cv2.cvtColor(np.array(images[page_node.metadata.number - start_page]), cv2.COLOR_BGR2RGB)
                page_node = PageNodeWrapper.wrap(page_node).set_orig_image(page_image)
                result_nodes.append(page_node)

        return NodeProcessorResult(changed_nodes=result_nodes)
