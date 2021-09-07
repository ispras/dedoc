import logging
import os
from typing import Optional, List

from dedoc.attachment_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.docx_reader.data_structures.docx_document import DocxDocument
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor


class DocxReader(BaseReader):
    def __init__(self, *, config: dict):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()
        self.attachment_extractor = DocxAttachmentsExtractor()
        self.logger = config.get("logger", logging.getLogger())

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

        lines = self.__fix_lines(docx_document.lines)
        return UnstructuredDocument(lines=lines, tables=docx_document.tables, attachments=attachments, warnings=[])

    def __fix_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        for i, line in enumerate(lines[1:]):
            if lines[i].hierarchy_level != line.hierarchy_level:
                continue

            if lines[i].hierarchy_level.paragraph_type != HierarchyLevel.raw_text:
                continue

            if lines[i].line.endswith('\n'):
                continue

            lines[i].set_line(lines[i].line + '\n')

            for annotation in lines[i].annotations:
                if annotation.end == len(lines[i].line) - 1:
                    annotation.end += 1

        return lines

    def _parse_document(self, path: str) -> DocxDocument:
        docx_document = DocxDocument(path=path,
                                     hierarchy_level_extractor=self.hierarchy_level_extractor,
                                     logger=self.logger)
        return docx_document
