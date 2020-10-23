from abc import ABC, abstractmethod
from typing import Optional

from data_structures.document_content import DocumentContent
from data_structures.unstructured_document import UnstructuredDocument


class AbstractStructureConstructor(ABC):
    """
    This class construct structurized document from unstructure document (list of lines). Structurized document may
    be represented as tree or something like that
    """

    @abstractmethod
    def structure_document(self,
                           document: UnstructuredDocument,
                           structure_type: Optional[str] = None) -> DocumentContent:
        """
        take into input unstructured document and build document with structure, for example tree
        """
        pass
