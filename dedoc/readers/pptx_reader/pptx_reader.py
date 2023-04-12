import os
from typing import Optional

from pptx import Presentation

from dedoc.attachments_extractors.concrete_attachments_extractors.pptx_attachments_extractor import PptxAttachmentsExtractor
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader


class PptxReader(BaseReader):
    def __init__(self, *, config: dict) -> None:
        self.attachments_extractor = PptxAttachmentsExtractor()

    def can_read(self, path: str, mime: str, extension: str, document_type: str, parameters: Optional[dict] = None) -> bool:
        return extension.lower() in recognized_extensions.pptx_like_format or mime in recognized_mimes.pptx_like_format

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        parameters = {} if parameters is None else parameters
        prs = Presentation(path)
        lines, tables = [], []

        for page_id, slide in enumerate(prs.slides, start=1):
            for paragraph_id, shape in enumerate(slide.shapes, start=1):

                if shape.has_text_frame:
                    lines.append(LineWithMeta(line=shape.text, metadata=LineMetadata(page_id=page_id, line_id=paragraph_id), annotations=[]))

                if shape.has_table:
                    cells = [[cell.text for cell in row.cells] for row in shape.table.rows]
                    tables.append(Table(cells=cells, metadata=TableMetadata(page_id=page_id)))

        attachments = self.attachments_extractor.get_attachments(tmpdir=os.path.dirname(path), filename=os.path.basename(path), parameters=parameters)

        return UnstructuredDocument(lines=lines, tables=tables, attachments=attachments, warnings=[])
