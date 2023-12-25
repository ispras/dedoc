import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from dedoc.config import get_config
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.stub_hierarchy_level_builder import StubHierarchyLevelBuilder
from dedoc.structure_extractors.line_type_classifiers.law_classifier import LawLineTypeClassifier


class AbstractLawStructureExtractor(AbstractStructureExtractor, ABC):
    """
    This class is used for extraction structure from laws.

    You can find the description of this type of structure in the section :ref:`law_structure`.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        """
        :param config: some configuration for document parsing
        """
        super().__init__(config=config)
        path = os.path.join(get_config()["resources_path"], "line_type_classifiers")
        self.classifier = LawLineTypeClassifier(classifier_type="law", path=os.path.join(path, "law_classifier.pkl.gz"), config=self.config)
        self.txt_classifier = LawLineTypeClassifier(classifier_type="law_txt", path=os.path.join(path, "law_txt_classifier.pkl.gz"), config=self.config)
        self.hierarchy_level_builders = [StubHierarchyLevelBuilder()]
        self.hl_type = "law"
        self.init_hl_depth = 1
        self.except_words = {"приказ", "положение", "требования", "постановление", "перечень", "регламент", "закон"}

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Extract law structure from the given document and add additional information to the lines' metadata.
        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """
        if document.metadata.get("file_type") in recognized_mimes.txt_like_format:
            document.lines = self.__preprocess_lines(document.lines)
            predictions = self.txt_classifier.predict(document.lines)
        else:
            predictions = self.classifier.predict(document.lines)
        labels = self._fix_labels(predictions)

        header_lines = []
        body_lines = []
        applications_lines = []
        cellar_lines = []

        is_body_begun = False
        is_application_begun = False
        is_cellar_begun = False
        for line, label in zip(document.lines, labels):
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

        header_lines = self.__call_builder("header", lines_with_labels=header_lines)
        body_lines = self.__call_builder("body", lines_with_labels=body_lines)
        cellar_lines = self.__call_builder("cellar", lines_with_labels=cellar_lines)
        applications_lines = self.__call_builder("application", lines_with_labels=applications_lines)
        document.lines = self._postprocess_lines(header_lines + body_lines + cellar_lines + applications_lines)

        return document

    def __preprocess_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        fixed_lines = []

        for line in lines:
            words = [word for word in line.line.split() if word.isalnum()]
            words_len = [len(w) for w in words]

            if len(words) > 0 and max(words_len) == 1:
                word = "".join(words)
                if word.lower() in self.except_words:
                    word += "\n"
                    line = LineWithMeta(line=word, metadata=line.metadata, annotations=line.annotations, uid=line.uid)
                    fixed_lines.append(line)
                    continue

            fixed_lines.append(line)

        return fixed_lines

    @abstractmethod
    def _postprocess_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        pass

    def __call_builder(self, start_tag: str, lines_with_labels: List[Tuple[LineWithMeta, str]]) -> List[LineWithMeta]:
        for builder in self.hierarchy_level_builders:
            if builder.can_build(start_tag, self.hl_type):
                return builder.get_lines_with_hierarchy(lines_with_labels=lines_with_labels, init_hl_depth=self.init_hl_depth)
        raise ValueError(f"No one can handle {start_tag} {self.hl_type}")

    def _fix_labels(self, labels: List[str]) -> List[str]:
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

        assert title_end <= application_start, f"{title_end} <= {application_start}"
        assert title_end <= last_body_unit, f"{title_end} <= {last_body_unit}"
        assert last_body_unit <= application_start, f"{last_body_unit} <= {application_start}"

        result = self.__get_result(application_start, labels, last_body_unit, title_end)
        return result

    def __get_result(self, application_start: int, labels: List[str], last_body_unit: int, title_end: int) -> List[str]:
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

    def _postprocess_roman(self, hierarchy_level: HierarchyLevel, line: LineWithMeta) -> LineWithMeta:
        if hierarchy_level.line_type == "subsection" and LawTextFeatures.roman_regexp.match(line.line):
            match = LawTextFeatures.roman_regexp.match(line.line)
            prefix = line.line[match.start(): match.end()]
            suffix = line.line[match.end():]
            symbols = [("T", "I"), ("Т", "I"), ("У", "V"), ("П", "II"), ("Ш", "III"), ("Г", "I")]
            for symbol_from, symbol_to in symbols:
                prefix = prefix.replace(symbol_from, symbol_to)
            line.set_line(prefix + suffix)
        return line

    def __finish_chunk(self, is_application_begun: bool, lines_with_labels: List[Tuple[LineWithMeta, str]]) -> List[LineWithMeta]:
        if len(lines_with_labels) == 0:
            return []

        if is_application_begun:
            return self.__call_builder("application", lines_with_labels)
        else:
            return self.__call_builder("body", lines_with_labels)
