from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.unstructured_document import UnstructuredDocument


class AbstractStructureConstructor(ABC):
    """
    This class construct structurized document from unstructure document (list of lines). Structurized document may
    be represented as tree or something like that
    """

    @abstractmethod
    def structure_document(self,
                           document: UnstructuredDocument,
                           version: str,
                           structure_type: Optional[str] = None) -> ParsedDocument:
        """
        take into input unstructured document and build document with structure, for example tree
        """
        pass
