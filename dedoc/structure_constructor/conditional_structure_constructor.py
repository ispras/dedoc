from typing import Optional, Dict

from common.exceptions.structure_extractor_exception import StructureExtractorException
from data_structures.document_content import DocumentContent
from data_structures.unstructured_document import UnstructuredDocument
from structure_constructor.abstract_structure_constructor import AbstractStructureConstructor


class ConditionalStructureExtractor(AbstractStructureConstructor):

    def __init__(self,
                 extractors: Dict[str, AbstractStructureConstructor],
                 default_extractor: AbstractStructureConstructor):
        self.extractors = extractors
        self.default_extractor = default_extractor

    def structure_document(self,
                           document: UnstructuredDocument,
                           structure_type: Optional[str] = None) -> DocumentContent:
        if structure_type in self.extractors:
            return self.extractors[structure_type].structure_document(document, structure_type)
        elif structure_type is None or structure_type == "":
            return self.default_extractor.structure_document(document, structure_type)
        else:
            raise StructureExtractorException("Bad structure type {}, available structure types is: {}".format(
                structure_type, " ".join(self.extractors.keys())
            ))
