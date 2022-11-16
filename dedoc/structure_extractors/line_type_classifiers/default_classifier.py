from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import AbstractPickledLineTypeClassifier
from dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier


class DefaultLineTypeClassifier(AbstractPickledLineTypeClassifier):

    document_type = "other"

    def get_predict_labels(self, lines: List[LineWithMeta]) -> List[str]:
        pass

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.__hierarchy_extractor = DefaultStructureExtractor()

    def predict(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        return self.__hierarchy_extractor.get_hierarchy_level(lines)

    @staticmethod
    def load_pickled(path: str, *, config: dict) -> AbstractLineTypeClassifier:
        return DefaultLineTypeClassifier(config=config)
