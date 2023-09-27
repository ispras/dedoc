import re
from typing import List

import numpy as np

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import AbstractPickledLineTypeClassifier


class LawLineTypeClassifier(AbstractPickledLineTypeClassifier):

    def __init__(self, classifier_type: str, path: str, *, config: dict) -> None:
        super().__init__(config=config)
        self.classifier, feature_extractor_parameters = self.load(classifier_type, path)
        self.feature_extractor = LawTextFeatures(**feature_extractor_parameters)
        self.regexp_application_begin = re.compile(
            r"^(\'|\")?((приложение)|(утвержден)[оаы]?){1}(( )*([№n]?( )*(\d){1,3})?( )*)"
            r"((к распоряжению)|(к постановлению)|(к приказу))?\s*$")

    def predict(self, lines: List[LineWithMeta]) -> List[str]:
        if len(lines) == 0:
            return []

        features = self.feature_extractor.transform([lines])
        labels_probability = self.classifier.predict_proba(features)  # noqa

        # mark lines inside quotes as raw_text
        inside_quotes = np.array(LawTextFeatures()._inside_quotes(lines), dtype=bool)  # noqa
        raw_text_id = list(self.classifier.classes_).index("raw_text")
        labels_probability[inside_quotes, raw_text_id] = 1
        labels = [self.classifier.classes_[label_id] for label_id in labels_probability.argmax(1)]
        content_start = [line_id for line_id, (label, line) in enumerate(zip(labels, lines)) if self.__match_body_begin(line.line, label)]
        header_end = min(content_start) if len(content_start) else len(labels) - 1
        # preparing header_id features
        header_id = list(self.classifier.classes_).index("header")
        labels_probability[header_end:, header_id] = 0
        labels_probability[:header_end, :] = 0
        labels_probability[:header_end, header_id] = 1
        # update labels
        labels = [self.classifier.classes_[label_id] for label_id in labels_probability.argmax(1)]
        return labels

    def __match_body_begin(self, text: str, label: str) -> bool:
        body_started = label in ("header", "raw_text") and any(regexp.match(text.strip()) for regexp in LawTextFeatures.named_regexp)
        application_started = self.regexp_application_begin.match(text.lower().strip())
        return label == "structure_unit" or body_started or application_started
