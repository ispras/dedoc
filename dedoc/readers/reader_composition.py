import inspect
import os
import warnings
from typing import Dict, List

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import splitext_, get_file_mime_type


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

    def parse_file(self, tmp_dir: str, filename: str, parameters: Dict[str, str]) -> UnstructuredDocument:
        """
        Get intermediate representation for the document of any format which one of the available readers can parse.
        If there is no suitable reader for the given document, the BadFileFormatException will be raised.

        :param tmp_dir: the directory where the file is located
        :param filename: name of the given file
        :param parameters: dict with additional parameters for document reader (as language for scans or delimiter for csv)
        :return: intermediate representation of the document with lines, tables and attachments
        """
        name, extension = splitext_(filename)
        file_path = os.path.join(tmp_dir, filename)
        mime = get_file_mime_type(file_path)
        document_type = parameters.get("document_type")

        for reader in self.readers:
            if "parameters" in inspect.getfullargspec(reader.can_read).args:
                can_read = reader.can_read(path=file_path, mime=mime, extension=extension, document_type=document_type, parameters=parameters)
            else:
                warnings.warn("!WARNING! you reader requires an update\n" +
                              "Please specify parameters argument in method can_read in {}\n".format(reader) +
                              " This parameters would be mandatory in the near future")
                can_read = reader.can_read(path=file_path, mime=mime, extension=extension, document_type=document_type)

            if can_read:
                unstructured_document = reader.read(path=file_path, document_type=document_type, parameters=parameters)
                assert len(unstructured_document.lines) == 0 or isinstance(unstructured_document.lines[0], LineWithMeta)
                assert isinstance(unstructured_document, UnstructuredDocument)  # TODO remove
                return unstructured_document

        raise BadFileFormatException(
            msg=f"No one can read file: name = {filename}, extension = {extension}, mime = {mime}, document type = {document_type}",
            msg_api=f"Unsupported file format {mime} of the input file {filename}"
        )
