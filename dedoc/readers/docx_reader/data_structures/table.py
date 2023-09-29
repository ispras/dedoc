import hashlib
from typing import List

from bs4 import Tag

from dedoc.data_structures import LineWithMeta
from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.readers.docx_reader.data_structures.utils import ParagraphMaker
from dedoc.readers.docx_reader.line_with_meta_converter import LineWithMetaConverter


class DocxTable:
    def __init__(self, xml: Tag, paragraph_maker: ParagraphMaker) -> None:
        """
        Contains information about table properties.
        :param xml: BeautifulSoup tree with table properties
        """
        self.xml = xml
        self.paragraph_maker = paragraph_maker
        self.__uid = hashlib.md5(xml.encode()).hexdigest()

    @property
    def uid(self) -> str:
        return self.__uid

    def to_table(self) -> Table:
        """
        Converts xml file with table to Table class
        """
        # tbl -- table; tr -- table row, tc -- table cell
        # delete tables inside tables
        for tbl in self.xml.find_all("w:tbl"):
            tbl.extract()

        rows = self.xml.find_all("w:tr")
        cell_list, rowspan_start_info = [], {}

        for row_index, row in enumerate(rows):
            cells = row.find_all("w:tc")
            cell_row_list, cell_ind = [], 0

            for cell in cells:
                # gridSpan tag describes number of horizontally merged cells
                grid_span = int(cell.gridSpan["w:val"]) if cell.gridSpan else 1

                # get lines with meta of the cell
                cell_lines = self.__get_cell_lines(cell)

                # vmerge tag for vertically merged set of cells (or horizontally split cells)
                # attribute val may be "restart" or "continue" ("continue" if omitted)
                if cell.vMerge:
                    value = cell.vMerge.get("w:val", "continue")
                    if value == "continue":
                        cell_lines = cell_list[-1][cell_ind].lines
                        cell_row_list.append(CellWithMeta(lines=cell_lines, colspan=1, rowspan=1, invisible=True))
                        last_cell_rowspan = cell_list[rowspan_start_info[cell_ind]][cell_ind]
                        last_cell_rowspan.rowspan += 1
                        cell_list[rowspan_start_info[cell_ind]][cell_ind] = last_cell_rowspan
                    elif value == "restart":
                        rowspan_start_info[cell_ind] = row_index
                        cell_row_list.append(CellWithMeta(lines=cell_lines, colspan=grid_span, rowspan=1, invisible=False))
                else:
                    cell_row_list.append(CellWithMeta(lines=cell_lines, colspan=grid_span, rowspan=1, invisible=False))

                # split merged cells
                for _ in range(grid_span - 1):
                    cell_row_list.append(CellWithMeta(lines=cell_lines, colspan=1, rowspan=1, invisible=True))
                    cell_ind += 1
                cell_ind += 1

            cell_list.append(cell_row_list)

        return Table(cells=cell_list, metadata=TableMetadata(page_id=None, uid=self.uid))

    def __get_cell_lines(self, cell: Tag) -> List[LineWithMeta]:
        paragraph_list: List[Paragraph] = []
        lines: List[LineWithMeta] = []

        for paragraph_id, paragraph_xml in enumerate(cell.find_all("w:p")):
            paragraph = self.paragraph_maker.make_paragraph(paragraph_xml=paragraph_xml, paragraph_list=paragraph_list)
            paragraph_list.append(paragraph)
            lines.append(LineWithMetaConverter(paragraph, paragraph_id).line)

        return lines
