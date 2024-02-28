import os
from typing import Optional

from article_classifier import ArticleLineTypeClassifier

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth


class ArticleStructureExtractor(AbstractStructureExtractor):
    """
    This class is used for extraction structure from English articles
    """
    document_type = "article"

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        path = os.path.abspath(os.path.dirname(__file__))  # path to the directory where the classifier weights are located
        self.classifier = ArticleLineTypeClassifier(path=os.path.join(path, "article_classifier.pkl.gz"), config=self.config)

        self.named_item_keywords = ("abstract", "introduction", "related work", "conclusion", "references", "appendix", "acknowledgements")

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        predictions = self.classifier.predict(document.lines)
        assert len(predictions) == len(document.lines)

        for line, line_type in zip(document.lines, predictions):

            if line_type == "title":
                # for root, level_1=0, level_2=0, can_be_multiline=True
                line.metadata.hierarchy_level = HierarchyLevel.create_root()
                continue

            if line_type == "named_item":
                # for named_item, level_1=1,2, can_be_multiline=True
                line.metadata.hierarchy_level = self.__handle_named_item(line=line, prediction=line_type, level_1=1)

            if line_type in ("author", "affiliation", "reference"):
                line.metadata.hierarchy_level = HierarchyLevel(level_1=3, level_2=1, can_be_multiline=False, line_type=line_type)
                continue

            # for caption and raw_text, level_1=None, level_2=None, can_be_multiline=True
            line.metadata.hierarchy_level = HierarchyLevel.create_raw_text()
            line.metadata.hierarchy_level.line_type = line_type

        return document

    def __handle_named_item(self, line: LineWithMeta, prediction: str, level_1: int) -> HierarchyLevel:
        text = line.line.strip().lower()

        if text in self.named_item_keywords:
            # for standard headers like Introduction, Conclusion, etc.
            return HierarchyLevel(level_1=level_1, level_2=1, can_be_multiline=True, line_type=prediction)

        # get list depth for numerated headers, e.g. 1.1->2, 1.1.1->3, for lines without numeration -1 is returned
        item_depth = get_dotted_item_depth(text)

        if item_depth == -1:
            # for non-standard headers without numeration or continuation of multiline headers
            return HierarchyLevel(level_1=level_1 + 1, level_2=1, can_be_multiline=True, line_type=prediction)

        # for headers with numeration
        return HierarchyLevel(level_1=level_1, level_2=item_depth, can_be_multiline=True, line_type=prediction)
