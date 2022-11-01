from typing import Optional, Dict

from src.common.exceptions.structure_extractor_exception import StructureExtractorException
from src.data_structures.document_content import DocumentContent
from src.data_structures.unstructured_document import UnstructuredDocument
from src.structure_constructor.concreat_structure_constructors.abstract_structure_constructor import \
    AbstractStructureConstructor
from src.structure_constructor.table_patcher import TablePatcher


class StructureConstructorComposition(AbstractStructureConstructor):

    def __init__(self,
                 extractors: Dict[str, AbstractStructureConstructor],
                 default_extractor: AbstractStructureConstructor) -> None:
        self.extractors = extractors
        self.default_extractor = default_extractor
        self.table_patcher = TablePatcher()

    def structure_document(self,
                           document: UnstructuredDocument,
                           structure_type: Optional[str] = None,
                           parameters: dict = None) -> DocumentContent:
        if parameters is None:
            parameters = {}
        if parameters.get("insert_table", "False").lower() == "true":
            document = self.table_patcher.insert_table(document=document)
        if structure_type in self.extractors:
            return self.extractors[structure_type].structure_document(document, structure_type)
        elif structure_type is None or structure_type == "":
            return self.default_extractor.structure_document(document, structure_type)
        else:
            raise StructureExtractorException("Bad structure type {}, available structure types is: {}".format(
                structure_type, " ".join(self.extractors.keys())
            ))
