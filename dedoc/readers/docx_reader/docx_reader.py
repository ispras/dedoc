import os
from typing import Tuple, Optional

from dedoc.attachment_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.docx_reader.data_structures.docx_document import DocxDocument
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor


class DocxReader(BaseReader):
    def __init__(self):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()
        self.attachment_extractor = DocxAttachmentsExtractor()

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: Optional[str],
                 parameters: Optional[dict] = None) -> bool:
        return ((extension in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format) and
                not document_type)

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> UnstructuredDocument:
        docx_document = self._parse_document(path=path)
        attachments = self.attachment_extractor.get_attachments(tmpdir=os.path.dirname(path),
                                                                filename=os.path.basename(path),
                                                                parameters=parameters)
        return UnstructuredDocument(lines=docx_document.lines, tables=docx_document.tables, attachments=attachments)

    def _parse_document(self, path: str) -> DocxDocument:
        docx_document = DocxDocument(path=path, hierarchy_level_extractor=self.hierarchy_level_extractor)
        return docx_document
