from typing import Optional, Dict

from dedoc.common.exceptions.structure_extractor_exception import StructureExtractorException
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructors.abstract_structure_constructor import AbstractStructureConstructor
from dedoc.structure_constructors.table_patcher import TablePatcher


class StructureConstructorComposition(AbstractStructureConstructor):
    """
    This class allows to construct structure from any document according to the available list of structure constructors.
    The list of structure constructors and names of structure types for them is set via the class constructor.
    Each structure type defines some specific document representation, which is retrieved via the corresponding structure constructor.
    """
    def __init__(self, constructors: Dict[str, AbstractStructureConstructor], default_constructor: AbstractStructureConstructor) -> None:
        """
        :param constructors: mapping structure_type -> structure constructor, defined for certain structure representations
        :param default_constructor: the structure constructor, that will be used by default if the empty structure type is given
        """
        self.constructors = constructors
        self.default_constructor = default_constructor
        self.table_patcher = TablePatcher()

    def structure_document(self,
                           document: UnstructuredDocument,
                           version: str,
                           structure_type: Optional[str] = None,
                           parameters: Optional[dict] = None) -> ParsedDocument:
        """
        Construct the result document structure according to the `structure_type` parameter.
        If `structure_type` is empty string or None the default constructor will be used.
        To get the information about the parameters look at the documentation of :class:`~dedoc.structure_constructors.AbstractStructureConstructor`.
        """
        parameters = {} if parameters is None else parameters

        if parameters.get("insert_table", "False").lower() == "true":
            document = self.table_patcher.insert_table(document=document)

        if structure_type in self.constructors:
            return self.constructors[structure_type].structure_document(document, structure_type)

        if structure_type is None or structure_type == "":
            return self.default_constructor.structure_document(document, version, structure_type)

        raise StructureExtractorException(f"Bad structure type {structure_type}, available structure types is: {' '.join(self.constructors.keys())}")
