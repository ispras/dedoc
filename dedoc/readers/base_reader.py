import logging
from abc import ABC, abstractmethod
from typing import Optional, Set

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.utils.utils import get_mime_extension


class BaseReader(ABC):
    """
    This class is a base class for reading documents of any formats.
    It allows to check if the specific reader can read the document of some format and
    to get document's text with metadata, tables and attachments.

    The metadata (or annotations) of the text are various and may include text boldness and color, footnotes or links to tables.
    Some of the readers can also extract information about line type and hierarchy level (for example, list item) -
    this information is stored in the `tag_hierarchy_level` attribute of the class :class:`~dedoc.data_structures.LineMetadata`.
    """
    def __init__(self, *, config: Optional[dict] = None, recognized_extensions: Optional[Set[str]] = None, recognized_mimes: Optional[Set[str]] = None) -> None:
        """
        :param config: configuration of the reader, e.g. logger for logging
        :param recognized_extensions: set of supported files extensions with a dot, for example {.doc, .pdf}
        :param recognized_mimes: set of supported MIME types of files
        """
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())
        self._recognized_extensions = {} if recognized_extensions is None else recognized_extensions
        self._recognized_mimes = {} if recognized_mimes is None else recognized_mimes

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if this reader can handle the given file.
        You should provide at least one of the following parameters: file_path, extension, mime.

        :param file_path: path to the file in the file system
        :param mime: MIME type of a file
        :param extension: file extension, for example .doc or .pdf
        :param parameters: dict with additional parameters for document reader, see :ref:`parameters_description` for more details

        :return: True if this reader can handle the file, False otherwise
        """
        mime, extension = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in self._recognized_extensions or mime in self._recognized_mimes

    @abstractmethod
    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Read file from disk and extract text with annotations, tables and attachments from the document.
        The given file should have appropriate extension and mime type, so it should be checked by the method
        :meth:`~dedoc.readers.BaseReader.can_read`, which should return True beforehand.

        :param file_path: path to the file in the file system
        :param parameters: dict with additional parameters for document reader, see :ref:`parameters_description` for more details

        :return: intermediate representation of the document with lines, tables and attachments
        """
        pass

    def _postprocess(self, document: UnstructuredDocument) -> UnstructuredDocument:
        """
        Perform document postprocessing.
        """
        return document
