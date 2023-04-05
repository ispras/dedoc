import logging
import os
from typing import Optional, List

from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.docx_reader.data_structures.docx_document import DocxDocument
from dedoc.readers.utils.hierarchy_level_extractor import HierarchyLevelExtractor
from dedoc.data_structures.hierarchy_level import HierarchyLevel


class DocxReader(BaseReader):
    def __init__(self, *, config: dict) -> None:
        self.hierarchy_level_extractor = HierarchyLevelExtractor()
        self.attachment_extractor = DocxAttachmentsExtractor()
        self.logger = config.get("logger", logging.getLogger())

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str], parameters: Optional[dict] = None) -> bool:
        return extension.lower() in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        parameters = {} if parameters is None else parameters
        docx_document = self._parse_document(path=path)

        attachments = self.attachment_extractor.get_attachments(tmpdir=os.path.dirname(path),
                                                                filename=os.path.basename(path),
                                                                parameters=parameters)

        lines = self.__fix_lines(docx_document.lines)
        return UnstructuredDocument(lines=lines, tables=docx_document.tables, attachments=attachments, warnings=[])

    def __fix_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        for i, line in enumerate(lines[1:]):
            if lines[i].hierarchy_level != line.hierarchy_level \
                    or lines[i].hierarchy_level.paragraph_type != HierarchyLevel.raw_text \
                    or lines[i].line.endswith('\n'):
                continue

            lines[i].set_line(lines[i].line + '\n')

            for annotation in lines[i].annotations:
                if annotation.end == len(lines[i].line) - 1:
                    annotation.end += 1

        return lines

    def _parse_document(self, path: str) -> DocxDocument:
        docx_document = DocxDocument(path=path, hierarchy_level_extractor=self.hierarchy_level_extractor, logger=self.logger)
        return docx_document
