import logging
import os
from typing import Optional, List

from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.docx_reader.data_structures.docx_document import DocxDocument
from dedoc.data_structures.hierarchy_level import HierarchyLevel


class DocxReader(BaseReader):
    """
    This class is used for parsing documents with .docx extension.
    Please use :class:`~dedoc.converters.DocxConverter` for getting docx file from similar formats.
    """
    def __init__(self, *, config: dict) -> None:
        self.attachment_extractor = DocxAttachmentsExtractor()
        self.logger = config.get("logger", logging.getLogger())

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        return extension.lower() in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        docx_document = self._parse_document(path=path)
        attachments = self.attachment_extractor.get_attachments(tmpdir=os.path.dirname(path), filename=os.path.basename(path), parameters=parameters)
        lines = self.__fix_lines(docx_document.lines)
        return UnstructuredDocument(lines=lines, tables=docx_document.tables, attachments=attachments, warnings=[])

    def __fix_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        for i, line in enumerate(lines[1:]):
            if lines[i].metadata.tag_hierarchy_level != line.metadata.tag_hierarchy_level \
                    or lines[i].metadata.tag_hierarchy_level.line_type != HierarchyLevel.unknown \
                    or lines[i].line.endswith('\n'):
                continue

            old_len = len(lines[i].line)
            lines[i].set_line(lines[i].line + '\n')

            for annotation in lines[i].annotations:
                if annotation.end == old_len:
                    annotation.end += 1

        return lines

    def _parse_document(self, path: str) -> DocxDocument:
        docx_document = DocxDocument(path=path, logger=self.logger)
        return docx_document
