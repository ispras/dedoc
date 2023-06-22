import logging
import os
import pickle
from typing import Optional

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader


class NoteReader(BaseReader):
    """
    This class is used for parsing documents with .note.pickle extension.
    """
    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the reader, e.g. logger for logging
        """
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return extension.lower().endswith(".note.pickle")

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """

        try:
            with open(path, 'rb') as infile:
                note_dict = pickle.load(infile)
            text = note_dict['content']
            if isinstance(text, bytes):
                text = text.decode()
            lines = [LineWithMeta(line=text, annotations=[], metadata=LineMetadata(line_id=0, page_id=0))]
            unstructured = UnstructuredDocument(tables=[], lines=lines, attachments=[])

            return unstructured
        except Exception as e:
            self.logger.warning(f"Can't handle {path}\n{e}")
            raise BadFileFormatException(f"Bad note file:\n file_name = {os.path.basename(path)}. Seems note-format is broken")
