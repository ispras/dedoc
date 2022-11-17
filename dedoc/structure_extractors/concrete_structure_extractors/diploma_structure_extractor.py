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

    def __init__(self, path: str, *, config: dict):
        self.toc_extractor = TOCFeatureExtractor()
        self.header_builder = HeaderHierarchyLevelBuilder()
        self.toc_builder = TocBuilder()
        self.body_builder = DiplomaBodyBuilder()
        self.classifier = DiplomaLineTypeClassifier(path=path, config=config)

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        lines = self._replace_toc_lines(document.lines)
        # exclude found toc from predicting
        lines_without_toc = [line for line in lines if line.metadata.paragraph_type != "toc"]
        predictions = self.classifier.predict(lines_without_toc)

        header_lines = [(line, prediction) for line, prediction in zip(lines, predictions) if prediction == "title"]
        toc_lines = [(line, "toc") for line in lines if line.metadata.paragraph_type == "toc"]
        body_lines = [(line, prediction) for line, prediction in zip(lines, predictions) if prediction != "title"]

        header_lines = self.header_builder.get_lines_with_hierarchy(lines_with_labels=header_lines, init_hl_depth=0)
        toc_lines = self.toc_builder.get_lines_with_hierarchy(lines_with_labels=toc_lines, init_hl_depth=1)
        body_lines = self.body_builder.get_lines_with_hierarchy(lines_with_labels=body_lines, init_hl_depth=1)
        document.lines = header_lines + toc_lines + body_lines
        return document

    def _replace_toc_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        toc_lines = self.toc_extractor.get_toc(lines)
        toc_lines = [toc_item["line"] for toc_item in toc_lines]
        toc_pages = set(line.metadata.page_id for line in toc_lines)

        lines_wo_toc = []
        for line in lines:
            if line.metadata.page_id in toc_pages:
                if line.line.strip().lower() == "содержание":
                    toc_lines = [line] + toc_lines
            else:
                lines_wo_toc.append(line)

        for line in toc_lines:
            line.metadata.paragraph_type = "toc"
        lines = lines_wo_toc + toc_lines
        lines = sorted(lines, key=lambda x: (x.metadata.page_id, x.metadata.line_id))
        return lines
