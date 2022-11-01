from abc import ABC, abstractmethod
from typing import Optional

from src.data_structures.document_content import DocumentContent
from src.data_structures.parsed_document import ParsedDocument


class AbstractMetadataExtractor(ABC):

    @abstractmethod
    def can_extract(self,
                    doc: Optional[DocumentContent],
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        check if this extractor can handle given file. Return True if can handle and False otherwise

        :type doc: document content
        :type directory: path to directory where original file and converted file are located
        :type filename: name of file after rename (for example 23141.doc)
        :type converted_filename: name of file after rename and conversion (for example 23141.docx)
        :type original_filename: file name before rename
        :type parameters: additional parameters
        :type other_fields: other fields
        """
        pass

    @abstractmethod
    def add_metadata(self,
                     doc: Optional[DocumentContent],
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: Optional[dict] = None,
                     other_fields: Optional[dict] = None) -> ParsedDocument:
        """
        add metadata to doc. Use this method only if this extractor can_extract this file

        :type doc: document content
        :type directory: path to directory where original file and converted file are located
        :type filename: name of file after rename (for example 23141.doc)
        :type converted_filename: name of file after rename and conversion (for example 23141.docx)
        :type original_filename: file name before rename
        :type version: src version
        :type parameters: additional parameters
        :type other_fields: other fields
        """
        pass
