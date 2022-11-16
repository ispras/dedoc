from typing import Dict

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor


class StructureExtractorComposition(AbstractStructureExtractor):

    def __init__(self, extractors: Dict[str, AbstractStructureExtractor], default_key: str) -> None:
        self.extractors = extractors
        self.default_extractor_key = default_key

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        document_type = parameters.get("document_type", self.default_extractor_key)
        extractor = self.extractors.get(document_type, self.extractors[self.default_extractor_key])
        return extractor.extract_structure(document, parameters)
