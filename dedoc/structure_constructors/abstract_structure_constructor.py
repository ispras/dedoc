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
    Also, some other custom structure can be defined by the specific constructor.
    """

    @abstractmethod
    def construct(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> ParsedDocument:
        """
        Process unstructured document and build parsed document representation on this basis.

        :param document: intermediate representation of the document received from some structure extractor \
        (there should be filled hierarchy levels for all lines)
        :param parameters: additional parameters for document parsing, see :ref:`structure_type_parameters` for more details
        :return:  the structured representation of the given document
        """
        pass
