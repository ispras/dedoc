import os
import pickle
from typing import Optional

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_mime_extension


class NoteReader(BaseReader):
    """
    This class is used for parsing documents with .note.pickle extension.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower().endswith(".note.pickle")

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
