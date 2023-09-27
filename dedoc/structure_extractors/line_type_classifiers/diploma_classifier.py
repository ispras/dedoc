from typing import List, Optional

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.diploma_feature_extractor import DiplomaFeatureExtractor
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import AbstractPickledLineTypeClassifier


class DiplomaLineTypeClassifier(AbstractPickledLineTypeClassifier):

    def __init__(self, path: str, *, config: dict) -> None:
        super().__init__(config=config)
        self.classifier, feature_extractor_parameters = self.load("diploma", path)
        self.feature_extractor = DiplomaFeatureExtractor()

    def predict(self, lines: List[LineWithMeta], toc_lines: Optional[List[LineWithMeta]] = None) -> List[str]:
        if len(lines) == 0:
            return []

        features = self.feature_extractor.transform([lines], toc_lines=[toc_lines])
        labels_probability = self.classifier.predict_proba(features)

        title_id = list(self.classifier.classes_).index("title")
        raw_text_id = list(self.classifier.classes_).index("raw_text")
        toc_id = list(self.classifier.classes_).index("toc")
        labels_probability[:, toc_id] = 0  # actually we don't predict toc items

        # set empty lines as raw_text
        empty_line = [line.line.strip() == "" for line in lines]
        labels_probability[empty_line, :] = 0
        labels_probability[empty_line, raw_text_id] = 1

        # Work with a title
        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        first_non_title = 0
        for i, line in enumerate(lines):
            text_wo_spaces = "".join(line.line.lower().strip().split())
            match = self.feature_extractor.year_regexp.match(text_wo_spaces)

            if match is not None:
                first_non_title = i + 1
                break

            if labels[i] not in ("title", "raw_text"):
                first_non_title = i
                break

        # set probability to one for title before the body or toc
        labels_probability[:first_non_title, :] = 0
        labels_probability[:first_non_title, title_id] = 1
        # zeros probability for title after body of document has begun
        labels_probability[first_non_title:, title_id] = 0

        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        assert len(labels) == len(lines)
        return labels
