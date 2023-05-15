from abc import ABC, abstractmethod
from typing import Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument


class AbstractMetadataExtractor(ABC):
    """
    This class is responsible for extracting metadata from the documents of different formats.
    """
    @abstractmethod
    def can_extract(self,
                    document: UnstructuredDocument,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        Check if this extractor can handle the given file. Return True if the extractor can handle it and False otherwise.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.add_metadata` documentation to get the information about parameters.
        """
        pass

    @abstractmethod
    def add_metadata(self,
                     document: UnstructuredDocument,
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: Optional[dict] = None,
                     other_fields: Optional[dict] = None) -> UnstructuredDocument:
        """
        Add metadata to the document if possible, i.e. method :meth:`can_extract` returned True.

        :type document: document content that has been received from some of the readers
        :type directory: path to the directory where the original and converted files are located
        :type filename: name of the file after renaming (for example 23141.doc). \
        The file gets a new name during processing by the dedoc manager (if used)
        :type converted_filename: name of the file after renaming and conversion (for example 23141.docx)
        :type original_filename: name of the file before renaming
        :type version: version of the dedoc library
        :type parameters: additional parameters for document parsing
        :type other_fields: other fields that should be added to the document's metadata
        :return: document content with added metadata attribute (dict with information about the document)
        """
        pass
