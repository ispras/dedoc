import os
import pickle
from typing import Optional

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader


class NoteReader(BaseReader):
    """
    This class is used for parsing documents with .note.pickle extension.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions={".note.pickle"})

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """

        try:
            with open(file_path, "rb") as infile:
                note_dict = pickle.load(infile)
            text = note_dict["content"]
            if isinstance(text, bytes):
                text = text.decode()
            lines = [LineWithMeta(line=text)]
            unstructured = UnstructuredDocument(tables=[], lines=lines, attachments=[])

            return unstructured
        except Exception as e:
            self.logger.warning(f"Can't handle {file_path}\n{e}")
            raise BadFileFormatError(f"Bad note file:\n file_name = {os.path.basename(file_path)}. Seems note-format is broken")
