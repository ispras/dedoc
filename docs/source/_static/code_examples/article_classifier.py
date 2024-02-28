from typing import List, Optional

from article_feature_extractor import ArticleFeatureExtractor

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import AbstractPickledLineTypeClassifier


class ArticleLineTypeClassifier(AbstractPickledLineTypeClassifier):

    def __init__(self, path: str, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.classifier, feature_extractor_parameters = self.load("article", path)
        self.feature_extractor = ArticleFeatureExtractor()

    def predict(self, lines: List[LineWithMeta]) -> List[str]:
        if len(lines) == 0:
            return []

        features = self.feature_extractor.transform([lines])
        labels_probability = self.classifier.predict_proba(features)

        # set empty lines as raw_text
        raw_text_id = list(self.classifier.classes_).index("raw_text")
        empty_line = [line.line.strip() == "" for line in lines]
        labels_probability[empty_line, :] = 0
        labels_probability[empty_line, raw_text_id] = 1

        # work with a title
        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        first_non_title = 0
        for i, line in enumerate(lines):
            if "Abstract" in line.line or labels[i] not in ("title", "raw_text"):
                first_non_title = i
                break

        # probability=1 for title before the body, probability=0 for title after body of document has begun
        title_id = list(self.classifier.classes_).index("title")
        labels_probability[:first_non_title, :] = 0
        labels_probability[:first_non_title, title_id] = 1
        labels_probability[first_non_title:, title_id] = 0

        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        assert len(labels) == len(lines)
        return labels
