from abc import ABC, abstractmethod
from typing import Optional


class AbstractMetadataExtractor(ABC):
    """
    This class is responsible for extracting metadata from the documents of different formats.
    """
    @abstractmethod
    def can_extract(self,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        Check if this extractor can handle the given file. Return True if the extractor can handle it and False otherwise.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract_metadata` documentation to get the information about parameters.
        """
        pass

    @abstractmethod
    def extract_metadata(self,
                         directory: str,
                         filename: str,
                         converted_filename: str,
                         original_filename: str,
                         parameters: Optional[dict] = None,
                         other_fields: Optional[dict] = None) -> dict:
        """
        Extract metadata from file if possible, i.e. method :meth:`can_extract` returned True.

        :param directory: path to the directory where the original and converted files are located
        :param filename: name of the file after renaming (for example 23141.doc). \
        The file gets a new name during processing by the dedoc manager (if used)
        :param converted_filename: name of the file after renaming and conversion (for example 23141.docx)
        :param original_filename: name of the file before renaming
        :param parameters: additional parameters for document parsing
        :param other_fields: other fields that should be added to the document's metadata
        :return: dict with metadata information about the document
        """
        pass
