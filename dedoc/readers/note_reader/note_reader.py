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
    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        return extension.lower().endswith(".note.pickle")

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:

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
