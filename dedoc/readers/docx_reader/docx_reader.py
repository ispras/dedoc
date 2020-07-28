import re

from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor

from typing import List, Optional, Tuple

from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.data_structures.line_with_meta import LineWithMeta


class DocxReader(BaseReader):
    def __init__(self):
        self.remove_empty_paragraphs = True
        self.hierarchy_level_extractor = HierarchyLevelExtractor()

    def can_read(self, path: str, mime: str, extension: str, document_type: str) -> bool:
        return extension in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:
        document = Document(path)
        tables = [self._process_table(table) for table in document.tables]
        lines = self._get_lines(document)
        return UnstructuredDocument(lines=lines, tables=tables), True

    def _process_table(self, table: DocxTable) -> Table:
        cells = [[cell.text for cell in row.cells] for row in table.rows]
        metadata = TableMetadata(page_id=None)
        return Table(cells=cells, metadata=metadata)

    def _get_text(self, paragraph: Paragraph) -> str:
        xml = paragraph._element.xml
        xml_br = re.sub("<w:br/>", "<w:t>\n</w:t>", xml)
        xml_texts = re.findall(r'<w:t [^>]*>[\s\S]*?</w:t>|<w:t>[\s\S]*?</w:t>', xml_br)
        texts = [re.sub(r'</?w:t.*?>', "", text) for text in xml_texts]
        text = "".join(texts)
        return text

    def _iter_block_items(self, parent: Document):
        for child in parent.element.body.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)

    def _get_style_level(self, paragraph: Paragraph) -> Optional[int]:
        if paragraph.style:
            name = paragraph.style.name.lower()

            if re.match(r'heading \d', name):
                return int(name[len("heading "):]) - 1

        return None

    def _get_text_level(self, paragraph: Paragraph) -> Optional[int]:
        text = self._get_text(paragraph)

        if re.match(r"^(Глава|Параграф)\s*(\d\\.)*(\d\\.?)?", text):
            return 0

        if re.match(r"^(Статья|Пункт)\s*(\d\\.)*(\d\\.?)?", text):
            return 1

        return None

    def _get_section_level(self, paragraph: Paragraph) -> Optional[int]:
        if "<w:outlineLvl w:val=" in paragraph._element.xml:
            return int(re.findall(r'<w:outlineLvl w:val="\d+', paragraph._element.xml)[0][21:])

        style_level = self._get_style_level(paragraph)
        if style_level is not None:
            return style_level

        text_level = self._get_text_level(paragraph)
        if text_level is not None:
            return text_level

        return None

    def _get_lines(self, document: Document) -> List[LineWithMeta]:
        lines = []
        paragraph_id = 0

        for block in self._iter_block_items(document):
            if not isinstance(block, Paragraph):
                continue  # go only by paragraphs

            text = self._get_text(block)

            if self.remove_empty_paragraphs and text.isspace():
                continue

            paragraph_id += 1
            metadata = ParagraphMetadata(paragraph_type="raw_text",
                                         predicted_classes=None,
                                         page_id=0,
                                         line_id=paragraph_id)

            lines.append(LineWithMeta(line=text, hierarchy_level=None, metadata=metadata, annotations=[]))

        lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
        return lines

    def __get_doc(self, path) -> Document:
        return Document(path)


