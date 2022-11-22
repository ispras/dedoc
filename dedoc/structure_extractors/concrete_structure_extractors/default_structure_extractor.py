from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor


class DefaultStructureExtractor(AbstractStructureExtractor):
    document_type = "other"

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        for line in document.lines:
            if line.metadata.paragraph_type == line.hierarchy_level.paragraph_type:
                continue

            if line.metadata.paragraph_type == HierarchyLevel.unknown:
                line.metadata.paragraph_type = line.hierarchy_level.paragraph_type
            else:
                line.hierarchy_level.paragraph_type = line.metadata.paragraph_type

        return document
