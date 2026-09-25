from typing import Sequence, Type

import cv2
from PIL import Image
from dedocutils.preprocessing.orientation_classification import OrientationClassifier
from pydantic import Field
from tdm.abstract.datamodel import AbstractNode
from typing_extensions import Self

from dedoc_future.abstract import AbstractNodeProcessor, ExecMode, ImmutableBaseModel, NodeProcessorResult, Resource
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.helpers.artifacts.configuration import ARTIFACTS


class OrientationClassifierConfig(ImmutableBaseModel):
    model_path: str = Field(title="Path to model", default_factory=lambda: ARTIFACTS["orientation_classifier"].download())


class OrientationClassification(AbstractNodeProcessor[PageNode, PdfBaseConfig, OrientationClassifierConfig]):
    """
    Classify document page orientation in degrees [0, 90, 180, 270].
    """
    def __init__(self, config: OrientationClassifierConfig) -> None:
        self.classifier = OrientationClassifier(checkpoint_path=config.model_path)

    @property
    def label(self) -> str:
        return "orientation_classification"

    @property
    def resource(self) -> Resource:
        return Resource.GPU

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
    def deploy_config_type(self) -> Type[OrientationClassifierConfig]:
        return OrientationClassifierConfig

    @classmethod
    def from_config(cls, config: OrientationClassifierConfig) -> Self:
        return cls(config=config)

    @classmethod
    def can_process(cls, data: AbstractNode, config: PdfBaseConfig) -> bool:
        return super().can_process(data, config) and PageNodeWrapper.wrap(data).image is not None

    def process(self, data: Sequence[PageNode], config: PdfBaseConfig) -> NodeProcessorResult[PageNode]:
        nodes = [PageNodeWrapper.wrap(node) for node in data]  # TODO make decorator for wrapping
        images = [Image.fromarray(cv2.cvtColor(node.image, cv2.COLOR_BGR2RGB)) for node in nodes]
        angles = self.classifier.predict(images)
        result_nodes = [node.set_angle(angle) for node, angle in zip(nodes, angles)]
        return NodeProcessorResult(changed_nodes=result_nodes)
