from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.unstructured_document import UnstructuredDocument


class AbstractStructureConstructor(ABC):
    """
    This class construct structured representation of the document from unstructured document (list of lines).

    The result class :class:`~dedoc.data_structures.ParsedDocument` contains :class:`~dedoc.data_structures.DocumentContent`
    consisting of tables and the structure itself.
    This structure is formed based on the list of :class:`~dedoc.data_structures.LineWithMeta` with their types and hierarchy levels,
    that are retrieved with the help of some structure extractor.

    The order of the document lines and their hierarchy can be represented in different ways, e.g. standard tree of lines hierarchy.
    Also some other custom structure can be defined by the specific constructor.
    """

    @abstractmethod
    def structure_document(self, document: UnstructuredDocument, version: str, structure_type: Optional[str] = None) -> ParsedDocument:
        """
        Process unstructured document and build parsed document representation on this basis.

        :param document: intermediate representation of the document received from some structure extractor \
        (there should be filled hierarchy levels for all lines)
        :param version: current version of the dedoc library
        :param structure_type: type of the structure that should be retrieved for the document
        :return:  the structured representation of the given document
        """
        pass
