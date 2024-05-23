from typing import List

from bs4 import Tag

from dedoc.data_structures import LineWithMeta, Table
from dedoc.readers.docx_reader.data_structures.table import DocxTable
from dedoc.readers.pptx_reader.paragraph import PptxParagraph


class PptxTable(DocxTable):

    def __init__(self, xml: Tag, page_id: int) -> None:
        super().__init__(xml=xml, paragraph_maker=None)
        self.tag_key = "a"
        self.page_id = page_id

    def to_table(self) -> Table:
        table = super().to_table()
        table.metadata.page_id = self.page_id
        return table

    def _get_cell_lines(self, cell: Tag) -> List[LineWithMeta]:
        cell_lines = []

        for line_id, paragraph_xml in enumerate(cell.find_all(f"{self.tag_key}:p")):
            cell_lines.append(PptxParagraph(paragraph_xml).get_line_with_meta(line_id=line_id, page_id=self.page_id))
        return cell_lines
