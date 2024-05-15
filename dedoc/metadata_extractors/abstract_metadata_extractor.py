import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Set, Tuple

from dedoc.utils.utils import get_mime_extension


class AbstractMetadataExtractor(ABC):
    """
    This class is responsible for extracting metadata from the documents of different formats.
    """
    def __init__(self, *, config: Optional[dict] = None, recognized_extensions: Optional[Set[str]] = None, recognized_mimes: Optional[Set[str]] = None) -> None:
        """
        :param config: configuration of the extractor, e.g. logger for logging
        :param recognized_extensions: set of supported files extensions with a dot, for example {.doc, .pdf}
        :param recognized_mimes: set of supported MIME types of files
        """
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())
        self._recognized_extensions = {} if recognized_extensions is None else recognized_extensions
        self._recognized_mimes = {} if recognized_mimes is None else recognized_mimes

    def can_extract(self,
                    file_path: str,
                    converted_filename: Optional[str] = None,
                    original_filename: Optional[str] = None,
                    parameters: Optional[dict] = None,
                    mime: Optional[str] = None,
                    extension: Optional[str] = None) -> bool:
        """
        Check if this extractor can handle the given file.

        :param file_path: path to the file to extract metadata. \
        If dedoc manager is used, the file gets a new name during processing - this name should be passed here (for example 23141.doc)
        :param converted_filename: name of the file after renaming and conversion (if dedoc manager is used, for example 23141.docx), \
        by default it's a name from the file_path. Converted file should be located in the same directory as the file before converting.
        :param original_filename: name of the file before renaming (if dedoc manager is used), by default it's a name from the file_path
        :param parameters: additional parameters for document parsing, see :ref:`parameters_description` for more details
        :param mime: MIME type of a file
        :param extension: file extension, for example .doc or .pdf
        :return: True if the extractor can handle the given file and False otherwise
        """
        file_dir, file_name, converted_filename, original_filename = self._get_names(file_path, converted_filename, original_filename)
        converted_file_path = os.path.join(file_dir, converted_filename)
        mime, extension = get_mime_extension(file_path=converted_file_path, mime=mime, extension=extension)
        return extension.lower() in self._recognized_extensions or mime in self._recognized_mimes

    @abstractmethod
    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None) -> dict:
        """
        Extract metadata from file if possible, i.e. method :meth:`can_extract` returned True.

        :param file_path: path to the file to extract metadata. \
        If dedoc manager is used, the file gets a new name during processing - this name should be passed here (for example 23141.doc)
        :param converted_filename: name of the file after renaming and conversion (if dedoc manager is used, for example 23141.docx), \
        by default it's a name from the file_path. Converted file should be located in the same directory as the file before converting.
        :param original_filename: name of the file before renaming (if dedoc manager is used), by default it's a name from the file_path
        :param parameters: additional parameters for document parsing, see :ref:`parameters_description` for more details
        :return: dict with metadata information about the document
        """
        pass

    def _get_names(self, file_path: str, converted_filename: Optional[str], original_filename: Optional[str]) -> Tuple[str, str, str, str]:
        file_dir, file_name = os.path.split(file_path)
        converted_filename = file_name if converted_filename is None else converted_filename
        original_filename = file_name if original_filename is None else original_filename

        return file_dir, file_name, converted_filename, original_filename
