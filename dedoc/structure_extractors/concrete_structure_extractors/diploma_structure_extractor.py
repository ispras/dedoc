import re
from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor

from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TOCFeatureExtractor
from dedoc.structure_extractors.hierarchy_level_builders.diploma_builder.body_builder import DiplomaBodyBuilder
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.toc_builder.toc_builder import TocBuilder
from dedoc.structure_extractors.line_type_classifiers.diploma_classifier import DiplomaLineTypeClassifier


class DiplomaStructureExtractor(AbstractStructureExtractor):
    document_type = "diploma"

    def __init__(self, path: str, *, config: dict) -> None:
        self.toc_extractor = TOCFeatureExtractor()
        self.header_builder = HeaderHierarchyLevelBuilder()
        self.toc_builder = TocBuilder()
        self.body_builder = DiplomaBodyBuilder()
        self.classifier = DiplomaLineTypeClassifier(path=path, config=config)
        self.footnote_start_regexp = re.compile(r"^\d+ ")

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        lines = self._replace_toc_lines(document.lines)
        lines = self._replace_footnote_lines(lines)
        self._add_page_id_lines(lines)

        # exclude found toc from predicting
        lines_for_predict = [line for line in lines if line.metadata.paragraph_type not in ("toc", "page_id", "footnote")]
        predictions = self.classifier.predict(lines_for_predict)
        assert len(predictions) == len(lines_for_predict)
        for line, prediction in zip(lines_for_predict, predictions):
            line.metadata.paragraph_type = prediction

        header_lines = [(line, line.metadata.paragraph_type) for line in lines if line.metadata.paragraph_type == "title"]
        toc_lines = [(line, "toc") for line in lines if line.metadata.paragraph_type == "toc"]
        body_lines = [(line, line.metadata.paragraph_type) for line in lines if line.metadata.paragraph_type not in ("title", "toc")]

        header_lines = self.header_builder.get_lines_with_hierarchy(lines_with_labels=header_lines, init_hl_depth=0)
        toc_lines = self.toc_builder.get_lines_with_hierarchy(lines_with_labels=toc_lines, init_hl_depth=1)
        body_lines = self.body_builder.get_lines_with_hierarchy(lines_with_labels=body_lines, init_hl_depth=1)
        document.lines = header_lines + toc_lines + body_lines
        return document

    def _replace_toc_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        toc_lines = self.toc_extractor.get_toc(lines)
        toc_lines = [toc_item["line"] for toc_item in toc_lines]
        min_toc_line_id = min(line.metadata.line_id for line in toc_lines)
        max_toc_line_id = max(line.metadata.line_id for line in toc_lines)

        lines_wo_toc = []
        for line in lines:
            if line.metadata.line_id < min_toc_line_id and line.line.strip().lower() == "содержание":
                toc_lines = [line] + toc_lines
            elif not (min_toc_line_id <= line.metadata.line_id <= max_toc_line_id):
                lines_wo_toc.append(line)

        for line in toc_lines:
            line.metadata.paragraph_type = "toc"
        lines = lines_wo_toc + toc_lines
        lines = sorted(lines, key=lambda x: (x.metadata.page_id, x.metadata.line_id))
        return lines

    def _replace_footnote_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        fixed_lines = []
        current_footnote = None
        for line in lines:
            # usual case of simple line
            if line.metadata.paragraph_type != "footnote" and current_footnote is None:
                fixed_lines.append(line)

            # simple line, previous was a footnote
            elif line.metadata.paragraph_type != "footnote":
                fixed_lines.append(current_footnote)
                fixed_lines.append(line)
                current_footnote = None

            # first footnote
            elif current_footnote is None:
                current_footnote = line

            # new footnote after previous one
            elif self.footnote_start_regexp.match(line.line):
                fixed_lines.append(current_footnote)
                current_footnote = line

            # footnote continuation
            else:
                current_footnote += line

        if current_footnote is not None:
            fixed_lines.append(current_footnote)
        return fixed_lines

    def _add_page_id_lines(self, lines: List[LineWithMeta]) -> None:
        for i in range(1, len(lines) - 1):
            line = lines[i]
            if (lines[i - 1].metadata.page_id < line.metadata.page_id or line.metadata.page_id < lines[i + 1].metadata.page_id) \
                    and line.line.strip().isdigit():
                line.metadata.paragraph_type = "page_id"
