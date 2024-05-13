import logging
import os
from typing import List, Optional, Tuple

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_file_mime_by_content, get_mime_extension


class ReaderComposition(object):
    """
    This class allows to read any document of the predefined list of formats according to the available list of readers.
    The list of readers is set via the class constructor.
    The first suitable reader is used for parsing (the one whose method :meth:`~dedoc.readers.BaseReader.can_read` returns True), \
    so the order of the given readers is important.
    """
    def __init__(self, readers: List[BaseReader], *, config: Optional[dict] = None) -> None:
        """
        :param readers: the list of readers for documents of different formats that will be used for parsing
        :param config: configuration dictionary, e.g. logger for logging
        """
        self.config = {} if config is None else config
        self.logger = self.config.get("logger", logging.getLogger())
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
        mime, extension = get_mime_extension(file_path=file_path)

        # firstly, try to read file using its original extension
        document, exception = self.__call_readers(file_path=file_path, parameters=parameters, mime=mime, extension=extension)
        if document is not None:
            return document
        self.logger.warning(f'Could not read file with mime = "{mime}", extension = "{extension}", try to detect file mime by its content')

        # secondly, try to read file using mime obtained by file's content
        mime = get_file_mime_by_content(file_path)
        warning_message = f'Detected file mime = "{mime}"'
        self.logger.warning(warning_message)

        document, second_exception = self.__call_readers(file_path=file_path, parameters=parameters, mime=mime, extension="")
        if document is not None:
            document.warnings.append(warning_message)
            return document

        exception = exception or second_exception or BadFileFormatError(
            msg=f'No one can read file: name = "{file_name}", extension = "{extension}", mime = "{mime}"',
            msg_api=f'Unsupported file mime "{mime}" of the input file "{file_name}"'
        )
        raise exception

    def __call_readers(self, file_path: str, parameters: Optional[dict], mime: str, extension: str)\
            -> Tuple[Optional[UnstructuredDocument], Optional[BadFileFormatError]]:
        for reader in self.readers:
            if reader.can_read(file_path=file_path, mime=mime, extension=extension, parameters=parameters):
                try:
                    unstructured_document = reader.read(file_path=file_path, parameters=parameters)
                except BadFileFormatError as e:
                    return None, e

                return unstructured_document, None

        return None, None
