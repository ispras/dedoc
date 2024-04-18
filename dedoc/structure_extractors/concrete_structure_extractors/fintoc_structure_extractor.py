from typing import Optional

from dedoc.data_structures import UnstructuredDocument
from dedoc.structure_extractors import AbstractStructureExtractor


class FintocStructureExtractor(AbstractStructureExtractor):
    """
    This class is an implementation of the TOC extractor for the `FinTOC 2022 Shared task<https://wp.lancs.ac.uk/cfie/fintoc2022/>`_.
    The code is a modification of the winner's solution (ISP RAS team).

    You can find the description of this type of structure in the section :ref:`fintoc_structure`.
    """
    document_type = "fintoc"

    def extract(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """

        To get the information about the method's parameters look at the documentation of the class \
        :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.
        """

        return document
