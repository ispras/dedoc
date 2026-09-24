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
        result_nodes = []
        for node in data:
            page_num = node.metadata.number + 1
            images = convert_from_path(node.metadata.file_ref.content, first_page=page_num, last_page=page_num)
            image = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)
            result_node = PageNodeWrapper.wrap(node).set_orig_image(image)
            result_nodes.append(result_node)

        return NodeProcessorResult(changed_nodes=result_nodes)
