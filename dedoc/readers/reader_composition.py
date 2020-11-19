import os
from typing import Dict, List

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.utils import splitext_, get_file_mime_type


class ReaderComposition(object):

    def __init__(self, readers: List[BaseReader]):
        self.readers = readers

    def parse_file(self, tmp_dir: str, filename: str, parameters: Dict[str, str]) -> [UnstructuredDocument, bool]:

        name, extension = splitext_(filename)
        file_path = os.path.join(tmp_dir, filename)
        mime = get_file_mime_type(file_path)
        document_type = parameters.get("document_type")

        for reader in self.readers:
            if reader.can_read(path=file_path, mime=mime, extension=extension, document_type=document_type):
                unstructured_document, need_analyze_attachments = reader.read(path=file_path,
                                                                              document_type=document_type,
                                                                              parameters=parameters
                                                                              )
                assert len(unstructured_document.lines) == 0 or isinstance(unstructured_document.lines[0], LineWithMeta)
                assert isinstance(unstructured_document, UnstructuredDocument)  # TODO remove
                return unstructured_document, need_analyze_attachments

        raise BadFileFormatException(
            msg="no one can read file: name = {}, extension = {}, mime = {}, document type = {}".format(
                filename, extension, mime, document_type),
            msg_api="Unsupported file format {} of the input file {}".format(mime, filename)

        )
