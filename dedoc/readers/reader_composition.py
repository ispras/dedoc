import os
from typing import List, Optional

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_mime_extension


class ReaderComposition(object):
    """
    This class allows to read any document of the predefined list of formats according to the available list of readers.
    The list of readers is set via the class constructor.
    The first suitable reader is used for parsing (the one whose method :meth:`~dedoc.readers.BaseReader.can_read` returns True), \
    so the order of the given readers is important.
    """
    def __init__(self, readers: List[BaseReader]) -> None:
        """
        :param readers: the list of readers for documents of different formats that will be used for parsing
        """
        self.readers = readers

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        Get intermediate representation for the document of any format which one of the available readers can parse.
        If there is no suitable reader for the given document, the BadFileFormatException will be raised.

        :param file_path: path of the file to be parsed
        :param parameters: dict with additional parameters for document readers, see :ref:`parameters_description` for more details
        :return: intermediate representation of the document with lines, tables and attachments
        """
        file_name = os.path.basename(file_path)
        extension, mime = get_mime_extension(file_path=file_path)

        for reader in self.readers:
            if reader.can_read(file_path=file_path, mime=mime, extension=extension, parameters=parameters):
                unstructured_document = reader.read(file_path=file_path, parameters=parameters)
                return unstructured_document

        raise BadFileFormatError(
            msg=f"No one can read file: name = {file_name}, extension = {extension}, mime = {mime}",
            msg_api=f"Unsupported file format {mime} of the input file {file_name}"
        )
