from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.diploma_feature_extractor import DiplomaFeatureExtractor
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import \
    AbstractPickledLineTypeClassifier


class DiplomaLineTypeClassifier(AbstractPickledLineTypeClassifier):

    def __init__(self, path: str, *, config: dict) -> None:
        super().__init__(config=config)
        self.classifier, feature_extractor_parameters = self.load(path)
        self.feature_extractor = DiplomaFeatureExtractor()

    def predict(self, lines: List[LineWithMeta]) -> List[str]:
        if len(lines) == 0:
            return []

        features = self.feature_extractor.transform([lines])
        labels_probability = self.classifier.predict_proba(features)

        title_id = list(self.classifier.classes_).index("title")
        raw_text_id = list(self.classifier.classes_).index("raw_text")

        # set empty lines as raw_text
        empty_line = [line.line.strip() == "" for line in lines]
        labels_probability[empty_line, :] = 0
        labels_probability[empty_line, raw_text_id] = 1

        # Work with a title
        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        first_non_title = min((i for i, label in enumerate(labels) if label not in ["title", "raw_text"]), default=0)
        # set probability to one for title before the body or toc
        labels_probability[:first_non_title, :] = 0
        labels_probability[:first_non_title, title_id] = 1
        # zeros probability for title after body of document has begun
        labels_probability[first_non_title:, title_id] = 0

        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        assert len(labels) == len(lines)
        return labels
