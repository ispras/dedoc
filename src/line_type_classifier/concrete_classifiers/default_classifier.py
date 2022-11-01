from typing import List

from src.data_structures.line_with_meta import LineWithMeta
from src.line_type_classifier.abstract_pickled_classifier import AbstractPickledLineTypeClassifier
from src.line_type_classifier.abstract_scan_classifier import AbstractLineTypeClassifier
from src.utils.hierarchy_level_extractor import HierarchyLevelExtractor


class DefaultLineTypeClassifier(AbstractPickledLineTypeClassifier):

    document_type = "other"

    def get_predict_labels(self, lines: List[LineWithMeta]) -> List[str]:
        pass

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.__hierarchy_extractor = HierarchyLevelExtractor()

    def predict(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        return self.__hierarchy_extractor.get_hierarchy_level(lines)

    @staticmethod
    def load_pickled(path: str, *, config: dict) -> AbstractLineTypeClassifier:
        return DefaultLineTypeClassifier(config=config)
