from abc import ABC, abstractmethod
from typing import Optional


class AbstractMetadataExtractor(ABC):
    """
    This class is responsible for extracting metadata from the documents of different formats.
    """
    @abstractmethod
    def can_extract(self,
                    file_path: str,
                    converted_filename: Optional[str] = None,
                    original_filename: Optional[str] = None,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        Check if this extractor can handle the given file. Return True if the extractor can handle it and False otherwise.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract` documentation to get the information about parameters.
        """
        pass

    @abstractmethod
    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None,
                other_fields: Optional[dict] = None) -> dict:
        """
        Extract metadata from file if possible, i.e. method :meth:`can_extract` returned True.

        :param file_path: path to the file to extract metadata. \
        If dedoc manager is used, the file gets a new name during processing - this name should be passed here (for example 23141.doc)
        :param converted_filename: name of the file after renaming and conversion (if dedoc manager is used, for example 23141.docx), \
        by default it's a name from the file_path. Converted file should be located in the same directory as the file before converting.
        :param original_filename: name of the file before renaming (if dedoc manager is used), by default it's a name from the file_path
        :param parameters: additional parameters for document parsing, see :ref:`parameters_description` for more details
        :param other_fields: other fields that should be added to the document's metadata
        :return: dict with metadata information about the document
        """
        pass
