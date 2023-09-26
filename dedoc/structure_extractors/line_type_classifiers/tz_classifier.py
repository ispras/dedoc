from typing import List

import numpy as np

from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.tz_feature_extractor import TzTextFeatures
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import AbstractPickledLineTypeClassifier


class TzLineTypeClassifier(AbstractPickledLineTypeClassifier):

    def __init__(self, classifier_type: str, path: str, *, config: dict) -> None:
        super().__init__(config=config)
        self.classifier, feature_extractor_parameters = self.load(classifier_type, path)
        self.feature_extractor = TzTextFeatures(**feature_extractor_parameters)

    def predict(self, lines: List[LineWithMeta]) -> List[str]:
        """
        get predictions from xgb classifier and patch them according to our prior knowledge. For example we know that
        title can not be interrupted with other structures. Empty line can not be item or toc item (but can be part of
        title or raw_text), there are can not be toc items after body has begun
        @param lines:
        @return:
        """
        if len(lines) == 0:
            return []

        features = self.feature_extractor.transform([lines])
        labels_probability = self.classifier.predict_proba(features)

        title_id = list(self.classifier.classes_).index("title")
        toc_id = list(self.classifier.classes_).index("toc")
        raw_text_id = list(self.classifier.classes_).index("raw_text")

        empty_line = [line.line.strip() == "" for line in lines]
        labels_probability[empty_line, :] = 0
        labels_probability[empty_line, raw_text_id] = 1

        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]
        first_non_title = min((i for i, label in enumerate(labels) if label not in ["title", "raw_text"]), default=0)
        # set probability to one for title before the body or toc
        labels_probability[:first_non_title, :] = 0
        labels_probability[:first_non_title, title_id] = 1
        # zeros probability for title after body of document has begun
        labels_probability[first_non_title:, title_id] = 0

        # work with probability for toc
        auto_toc_lines_mask = np.array([self.__is_auto_toc_line(line) for line in lines])
        if auto_toc_lines_mask.any():
            #  include line with contents header to the toc e.g. "содержание"
            first_auto_toc_ind = np.where(auto_toc_lines_mask)[0][0]
            first_toc_ind = min((i for i, label in enumerate(labels) if label == "toc"), default=-1)
            if first_toc_ind > 0:
                auto_toc_lines_mask[first_toc_ind:first_auto_toc_ind] = True
            # zero probability for non-toc elements in documents with auto toc
            labels_probability[np.logical_not(auto_toc_lines_mask), toc_id] = 0
            # toc elements are definitely toc
            labels_probability[auto_toc_lines_mask, toc_id] = 1
        else:
            # zeros probability for toc after body begun
            first_item = min((i for i, label in enumerate(labels) if label in ("item", "part")), default=0)
            labels_probability[first_item:, toc_id] = 0
        toc_lines = (line_id for line_id, line in enumerate(lines) if line.line.strip().lower() == "содержание")
        toc_start_id = min(toc_lines, default=-1)
        if toc_id > 0:
            labels_probability[:toc_start_id, toc_id] = 0
        labels = [self.classifier.classes_[i] for i in labels_probability.argmax(1)]

        predictions = self._postprocess_labels(lines=lines, predictions=labels)
        assert len(predictions) == len(lines)
        return predictions

    def __is_auto_toc_line(self, line: LineWithMeta) -> bool:
        annotations = line.annotations
        for annotation in annotations:
            if annotation.name == "style":
                return annotation.value.lower().startswith("toc") or annotation.value.lower().startswith("contents")
        return False

    def _postprocess_labels(self, lines: List[LineWithMeta], predictions: List[str]) -> List[str]:
        assert len(lines) == len(predictions)
        sizes = [self._get_size(line) for line in lines]
        median_size = np.median(sizes)
        result = []
        for line, prediction in zip(lines, predictions):
            if self._get_size(line) >= median_size + 2 and prediction in ("item", "part", "named_item"):
                result.append("part")
            elif prediction == "part":
                result.append("named_item")
            else:
                result.append(prediction)
        return result

    def _get_size(self, line: LineWithMeta) -> float:
        caps = 1 if line.line.isupper() and len(line.line.strip()) > 4 else 0
        for annotation in line.annotations:
            if annotation.name == SizeAnnotation.name:
                return float(annotation.value) + caps
        return 0 + caps
