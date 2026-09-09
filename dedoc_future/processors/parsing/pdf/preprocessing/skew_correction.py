from typing import Callable, Sequence, Type

from dedocutils.preprocessing import SkewCorrector
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper


class SkewCorrection(AbstractProcessor[PageNode, PdfBaseConfig, ImmutableBaseModel]):
    """
    Skew correction of the page image (for small angles < 45 degrees).
    """
    def __init__(self) -> None:
        self.skew_corrector = SkewCorrector()

    @property
    def label(self) -> str:
        return "skew_correction"

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
    def deploy_config_type(self) -> Type[ImmutableBaseModel]:
        return ImmutableBaseModel

    @classmethod
    def from_config(cls, config: ImmutableBaseModel) -> Self:
        return cls()

    @property
    def predicate(self) -> Callable[[TalismanDocument, PageNode, PdfBaseConfig], bool]:
        def check_node(document: TalismanDocument, node: PageNode, config: PdfBaseConfig) -> bool:
            return PageNodeWrapper.wrap(node).image is not None

        return check_node

    def process(self, document: TalismanDocument, nodes: Sequence[PageNode], config: PdfBaseConfig) -> ProcessorResult[PageNode]:
        result_nodes = []
        for node in nodes:
            node = PageNodeWrapper.wrap(node)
            parameters_dict = {} if node.angle is None else {"orientation_angle": node.angle}
            rotated_image, angle_dict = self.skew_corrector.preprocess(image=node.image, parameters=parameters_dict)
            result_nodes.append(node.set_image(rotated_image).set_angle(angle_dict["rotated_angle"]))

        return ProcessorResult(nodes=result_nodes, structure={})
