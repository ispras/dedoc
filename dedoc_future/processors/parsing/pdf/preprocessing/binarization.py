from typing import Callable, Sequence, Type

from dedocutils.preprocessing import AdaptiveBinarizer
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper


class BinarizerConfig(ImmutableBaseModel):
    block_size: int = 40
    delta: int = 40


class Binarizer(AbstractProcessor[PageNode, PdfBaseConfig, BinarizerConfig]):
    """
    Turns colored pages images into black-and-white.
    """
    def __init__(self, config: BinarizerConfig) -> None:
        self.binarizer = AdaptiveBinarizer(block_size=config.block_size, delta=config.delta)

    @property
    def label(self) -> str:
        return "binarization"

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
    def node_type(self) -> Type[PageNode]:
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

    @property
    def predicate(self) -> Callable[[TalismanDocument, PageNode, PdfBaseConfig], bool]:
        def check_node(document: TalismanDocument, node: PageNode, config: PdfBaseConfig) -> bool:
            return PageNodeWrapper.wrap(node).image is not None

        return check_node

    def process(self, document: TalismanDocument, nodes: Sequence[PageNode], config: PdfBaseConfig) -> ProcessorResult[PageNode]:
        result_nodes = []
        for node in nodes:
            node = PageNodeWrapper.wrap(node)
            binarized_image, _ = self.binarizer.preprocess(image=node.image)
            result_nodes.append(node.set_image(binarized_image))

        return ProcessorResult(nodes=result_nodes, structure={})
