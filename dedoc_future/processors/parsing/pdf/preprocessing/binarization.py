from typing import Sequence, Type

from dedocutils.preprocessing import AdaptiveBinarizer
from tdm.abstract.datamodel import AbstractNode
from typing_extensions import Self

from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper


class BinarizerConfig(ImmutableBaseModel):
    block_size: int = 40
    delta: int = 40


class Binarizer(AbstractNodeProcessor[PageNode, PdfBaseConfig, BinarizerConfig]):
    """
    Turns colored pages images into black-and-white.
    """
    def __init__(self, config: BinarizerConfig) -> None:
        self.binarizer = AdaptiveBinarizer(block_size=config.block_size, delta=config.delta)

    @property
    def label(self) -> str:
        return "binarization"

    @property
    def resource(self) -> Resource:
        return Resource.CPU

    @property
    def exec_mode(self) -> ExecMode:
        return ExecMode.THREAD

    @classmethod
    def node_type(cls) -> Type[PageNode]:
        return PageNode

    @property
    def config_type(self) -> Type[PdfBaseConfig]:
        return PdfBaseConfig

    @property
    def deploy_config_type(self) -> Type[BinarizerConfig]:
        return BinarizerConfig

    @classmethod
    def from_config(cls, config: BinarizerConfig) -> Self:
        return cls(config=config)

    @classmethod
    def can_process(cls, data: AbstractNode, config: PdfBaseConfig) -> bool:
        return super().can_process(data, config) and PageNodeWrapper.wrap(data).image is not None

    def process(self, data: Sequence[PageNode], config: PdfBaseConfig) -> NodeProcessorResult[PageNode]:
        result_nodes = []
        for node in data:
            node = PageNodeWrapper.wrap(node)
            binarized_image, _ = self.binarizer.preprocess(image=node.image)
            result_nodes.append(node.set_image(binarized_image))

        return NodeProcessorResult(changed_nodes=result_nodes)
