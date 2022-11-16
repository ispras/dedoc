import gzip
import os
import pickle
import re
from abc import abstractmethod
from typing import List, Tuple, Iterator

import numpy as np
from xgboost import XGBClassifier

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.stub_hierarchy_level_builder import StubHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_ends_of_number
from dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier import AbstractPickledLineTypeClassifier


class AbstractLawLineTypeClassifier(AbstractPickledLineTypeClassifier):
    regexp_application_begin = re.compile(r"^(\'|\")?((приложение)|(утвержден)[оаы]?){1}(( )*([№n]?( )*(\d){1,3})?( )*)"
                                          r"((к распоряжению)|(к постановлению)|(к приказу))?\s*$")
    ends_of_number = regexps_ends_of_number

    def __init__(self, classifier: XGBClassifier, feature_extractor: LawTextFeatures, *, config: dict) -> None:
        super().__init__(config=config)
        self.__feature_extractor = feature_extractor
        self.__classifier = classifier
        self._chunk_hl_builders = [StubHierarchyLevelBuilder()]
        self.__init_hl_depth = 1
        self.chunk_start_tags = ["header", "body", "cellar", "application"]
        self.hl_type = "law"

    def predict(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        if len(lines) == 0:
            return lines
        result = self._add_line_labels(lines)
        return list(self._law_line_postprocess(result))

    @staticmethod
    def _load_gzipped_xgb(path: str) -> Tuple[XGBClassifier, dict]:
        if path is None:
            classifier_name = "law_classifier.pkl.gz"
            path = os.path.join(os.path.dirname(__file__), "..", "..", "resources/", classifier_name)
            path = os.path.abspath(path)
        with gzip.open(path) as file:
            classifier, feature_extractor_parameters = pickle.load(file)
            return classifier, feature_extractor_parameters

    @staticmethod
    def _postprocess_roman(hierarchy_level: HierarchyLevel, line: LineWithMeta) -> LineWithMeta:
        if hierarchy_level.paragraph_type == "subsection" and LawTextFeatures.roman_regexp.match(line.line):
            match = LawTextFeatures.roman_regexp.match(line.line)
            prefix = line.line[match.start(): match.end()]
            suffix = line.line[match.end():]
            symbols = [('T', 'I'), ('Т', 'I'), ('У', 'V'), ('П', "II"), ('Ш', "III"), ('Г', 'I')]
            for symbol_from, symbol_to in symbols:
                prefix = prefix.replace(symbol_from, symbol_to)
            line.set_line(prefix + suffix)
        return line

    def _get_predict_labels(self, lines: List[LineWithMeta]) -> [np.ndarray, List[str]]:
        features = self.__feature_extractor.transform([lines])
        labels_probability = self.__classifier.predict_proba(features)  # noqa
        labels = [self.__classifier.classes_[label_id] for label_id in labels_probability.argmax(1)]

        return [labels_probability, labels]

    def _add_line_labels(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        # 1 - prediction from all lines
        labels = self.__get_labels(lines)

        header_lines = []
        body_lines = []
        applications_lines = []
        cellar_lines = []

        is_body_begun = False
        is_application_begun = False
        is_cellar_begun = False
        for line, label in zip(lines, labels):
            if label == "structure_unit":
                is_body_begun = True
            elif label == "cellar":
                is_cellar_begun = True
            elif label == "application":
                is_application_begun = True

            if is_cellar_begun and not is_application_begun:
                cellar_lines.append((line, label))
            elif is_application_begun:
                applications_lines.append((line, label))
            elif is_body_begun:
                body_lines.append((line, label))
            else:
                header_lines.append((line, label))

        return (self.__call_builder("header", lines_with_labels=header_lines) +
                self.__call_builder("body", lines_with_labels=body_lines) +
                self.__call_builder("cellar", lines_with_labels=cellar_lines) +
                self.__call_builder("application", lines_with_labels=applications_lines))

    def __get_labels(self, lines: List[LineWithMeta]) -> List[str]:
        labels_probability, _ = self._get_predict_labels(lines)
        # mark lines inside quotes as raw_text
        inside_quotes = np.array(LawTextFeatures()._inside_quotes(lines), dtype=bool)  # noqa
        raw_text_id = list(self.__classifier.classes_).index("raw_text")
        labels_probability[inside_quotes, raw_text_id] = 1
        labels = [self.__classifier.classes_[label_id] for label_id in labels_probability.argmax(1)]
        content_start = [line_id for line_id, label in enumerate(labels)
                         if self.__match_body_begin(lines[line_id].line, label) or
                         self.regexp_application_begin.match(lines[line_id].line.lower().strip())]
        header_end = min(content_start) if len(content_start) else len(labels) - 1
        # preparing header_id features
        header_id = list(self.__classifier.classes_).index("header")
        labels_probability[header_end:, header_id] = 0
        labels_probability[:header_end, :] = 0
        labels_probability[:header_end, header_id] = 1
        # update labels
        labels = [self.__classifier.classes_[label_id] for label_id in labels_probability.argmax(1)]
        labels_fixed = self._fix_labels_with_document_model(labels)
        return labels_fixed

    def _fix_labels_with_document_model(self, labels: List[str]) -> List[str]:
        """
        document model for law if following:
        1 Title (before the first structure_unit)
        2 Body (from the first structure_unit to the cellar or application or the end of the document)
        3 Cellar (optional) after body, before the application
        4 Application (after cellar, can be mixed with structure_units and raw text)

        footer may be found in any place in the document

        :param labels: predicted labels
        :return: labels updated according to the document model
        """
        title_end = None
        application_start = None
        last_body_unit = None
        for index, label in enumerate(labels):
            if title_end is None and label in ("structure_unit", "cellar", "application"):
                title_end = index
            if application_start is None and label == "application":
                application_start = index
            if application_start is None and label == "structure_unit":
                last_body_unit = index
        if title_end is None:
            title_end = len(labels)
        if application_start is None:
            application_start = len(labels)
        if last_body_unit is None:
            last_body_unit = title_end

        assert title_end <= application_start, "{} <= {}".format(title_end, application_start)
        assert title_end <= last_body_unit, "{} <= {}".format(title_end, last_body_unit)
        assert last_body_unit <= application_start, "{} <= {}".format(last_body_unit, application_start)

        result = []
        for index, label in enumerate(labels):
            if label == "footer":
                result.append(label)
            elif index < title_end:
                result.append("title")
            elif title_end <= index < last_body_unit:
                if label in ("cellar", "title"):
                    result.append("raw_text")
                else:
                    result.append(label)
            elif last_body_unit <= index < application_start:
                if label == "title":
                    result.append("raw_text")
                else:
                    result.append(label)
            elif index >= application_start:
                if label in ("cellar", "title"):
                    result.append("raw_text")
                else:
                    result.append(label)
            else:
                ValueError("How i get here")
        assert len(result) == len(labels)
        return result

    @abstractmethod
    def _law_line_postprocess(self, lines: List[LineWithMeta]) -> Iterator[LineWithMeta]:
        pass

    def __call_builder(self, start_tag: str, lines_with_labels: List[Tuple[LineWithMeta, str]]) -> List[LineWithMeta]:
        for builder in self._chunk_hl_builders:
            if builder.can_build(start_tag, self.hl_type):
                return builder.get_lines_with_hierarchy(lines_with_labels=lines_with_labels,
                                                        init_hl_depth=self.__init_hl_depth)
        raise ValueError("no one can handle {} {}".format(start_tag, self.hl_type))

    def __match_body_begin(self, text: str, label: str) -> bool:
        return (label == "structure_unit" or
                label in ("header", "raw_text") and
                any(regexp.match(text.strip()) for regexp in LawTextFeatures.named_regexp))

    def __finish_chunk(self,
                       is_application_begun: bool,
                       lines_with_labels: List[Tuple[LineWithMeta, str]]) -> List[LineWithMeta]:
        if len(lines_with_labels) == 0:
            return []

        if is_application_begun:
            return self.__call_builder("application", lines_with_labels)
        else:
            return self.__call_builder("body", lines_with_labels)
