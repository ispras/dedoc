from typing import Sequence, Type

from dedocutils.preprocessing import SkewCorrector
from tdm.abstract.datamodel import AbstractNode
from typing_extensions import Self

from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper


class SkewCorrection(AbstractNodeProcessor[PageNode, PdfBaseConfig, ImmutableBaseModel]):
    """
    Skew correction of the page image (for small angles < 45 degrees).
    """
    def __init__(self) -> None:
        self.skew_corrector = SkewCorrector()

    @property
    def label(self) -> str:
        return "skew_correction"

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
    def deploy_config_type(self) -> Type[ImmutableBaseModel]:
        return ImmutableBaseModel

    @classmethod
    def from_config(cls, config: ImmutableBaseModel) -> Self:
        return cls()

    @classmethod
    def can_process(cls, data: AbstractNode, config: PdfBaseConfig) -> bool:
        return super().can_process(data, config) and PageNodeWrapper.wrap(data).image is not None

    def process(self, data: Sequence[PageNode], config: PdfBaseConfig) -> NodeProcessorResult[PageNode]:
        result_nodes = []
        for node in data:
            node = PageNodeWrapper.wrap(node)
            parameters_dict = {} if node.angle is None else {"orientation_angle": node.angle}
            rotated_image, angle_dict = self.skew_corrector.preprocess(image=node.image, parameters=parameters_dict)
            result_nodes.append(node.set_image(rotated_image).set_angle(angle_dict["rotated_angle"]))

        return NodeProcessorResult(changed_nodes=result_nodes)
