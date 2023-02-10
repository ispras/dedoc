import os
from typing import Optional

from pptx import Presentation

from dedoc.attachments_extractors.concrete_attachments_extractors.pptx_attachments_extractor import PptxAttachmentsExtractor
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.utils.hierarchy_level_extractor import HierarchyLevelExtractor


class PptxReader(BaseReader):
    def __init__(self, *, config: dict) -> None:
        self.hierarchy_level_extractor = HierarchyLevelExtractor()
        self.attachments_extractor = PptxAttachmentsExtractor(need_content_analysis=config.get("need_content_analysis", True))

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: str,
                 parameters: Optional[dict] = None) -> bool:
        return extension.lower() in recognized_extensions.pptx_like_format or mime in recognized_mimes.pptx_like_format

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> UnstructuredDocument:
        prs = Presentation(path)
        lines, tables = [], []

        for page_id, slide in enumerate(prs.slides, start=1):
            for paragraph_id, shape in enumerate(slide.shapes, start=1):

                if shape.has_text_frame:
                    metadata = ParagraphMetadata(paragraph_type=HierarchyLevel.unknown,
                                                 predicted_classes=None,
                                                 page_id=page_id,
                                                 line_id=paragraph_id)
                    lines.append(LineWithMeta(line=shape.text, hierarchy_level=None, metadata=metadata, annotations=[]))

                if shape.has_table:
                    cells = [[cell.text for cell in row.cells] for row in shape.table.rows]
                    metadata = TableMetadata(page_id=page_id)
                    tables.append(Table(cells=cells, metadata=metadata))

        lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
        attachments = self.attachments_extractor.get_attachments(tmpdir=os.path.dirname(path),
                                                                 filename=os.path.basename(path),
                                                                 parameters=parameters)

        return UnstructuredDocument(lines=lines, tables=tables, attachments=attachments, warnings=[])
