from typing import Callable, Sequence, Type

import numpy as np
from PIL import Image
from dedocutils.preprocessing.orientation_classification import OrientationClassifier
from pydantic import BaseModel
from tdm import TalismanDocument
from typing_extensions import Self

from dedoc_future.abstract import AbstractProcessor, ExecMode, Resource, Scope
from dedoc_future.abstract.processor import ProcessorResult
from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper


class OrientationClassifierConfig(BaseModel):
    model_path: str


class OrientationClassification(AbstractProcessor[PageNode, PdfBaseConfig, OrientationClassifierConfig]):
    """
    Classify document page orientation in degrees [0, 90, 180, 270].
    """
    def __init__(self, config: OrientationClassifierConfig) -> None:
        self.classifier = OrientationClassifier(checkpoint_path=config.model_path)

    @property
    def label(self) -> str:
        return "orientation_classification"

    @property
    def scope(self) -> Scope:
        return Scope.NODE

    @property
    def resource(self) -> Resource:
        return Resource.GPU

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
    def deploy_config_type(self) -> Type[OrientationClassifierConfig]:
        return OrientationClassifierConfig

    @classmethod
    def from_config(cls, config: OrientationClassifierConfig) -> Self:
        return cls(config=config)

    @property
    def predicate(self) -> Callable[[TalismanDocument, PageNode, PdfBaseConfig], bool]:
        def check_node(document: TalismanDocument, node: PageNode, config: PdfBaseConfig) -> bool:
            return PageNodeWrapper.wrap(node).image is not None

        return check_node

    def process(self, document: TalismanDocument, nodes: Sequence[PageNode], config: PdfBaseConfig) -> ProcessorResult[PageNode]:
        nodes = [PageNodeWrapper.wrap(node) for node in nodes]  # TODO make decorator for wrapping
        images = [Image.fromarray(np.uint8(node.image)).convert("RGB") for node in nodes]
        angles = self.classifier.predict(images)
        result_nodes = [node.set_angle(angle) for node, angle in zip(nodes, angles)]
        return ProcessorResult(nodes=result_nodes, structure={})
