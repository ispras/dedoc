import hashlib
from collections import namedtuple
from bs4 import Tag

from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.readers.docx_reader.data_structures.run import Run
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor

CellPropertyInfo = namedtuple('NamedTuple', 'colspan, rowspan, invisible')


class DocxTable:
    def __init__(self, xml: Tag, styles_extractor: StylesExtractor) -> None:
        """
        Contains information about table properties.
        :param xml: BeautifulSoup tree with table properties
        """
        self.xml = xml
        self._uid = hashlib.md5(xml.encode()).hexdigest()
        self.styles_extractor = styles_extractor

    @property
    def uid(self) -> str:
        return self._uid

    def to_table(self) -> Table:
        """
        Converts xml file with table to Table class
        """
        # tbl -- table; tr -- table row, tc -- table cell
        result_cells = []

        # delete tables inside tables
        for tbl in self.xml.find_all("w:tbl"):
            tbl.extract()

        rows = self.xml.find_all("w:tr")
        prev_row, cell_property_list, rowspan_start_info = [], [], {}

        for row_index, row in enumerate(rows):
            cells = row.find_all("w:tc")
            cells_text, cell_property_row_list, cell_ind = [], [], 0

            for cell in cells:
                # gridSpan tag describes number of horizontally merged cells
                grid_span = int(cell.gridSpan["w:val"]) if cell.gridSpan else 1

                # get text of the cell
                cell_text = self.__get_cell_text(cell)

                # vmerge tag for vertically merged set of cells (or horizontally split cells)
                # attribute val may be "restart" or "continue" ("continue" if omitted)
                if cell.vMerge:
                    value = cell.vMerge.get("w:val", "continue")
                    if value == "continue":
                        cell_property_row_list.append(CellPropertyInfo(1, 1, True))
                        cell_text += prev_row[cell_ind]
                        last_cell_rowspan = cell_property_list[rowspan_start_info[cell_ind]][cell_ind]
                        cell_property_list[rowspan_start_info[cell_ind]][cell_ind] = last_cell_rowspan._replace(rowspan=last_cell_rowspan.rowspan + 1)
                    elif value == "restart":
                        rowspan_start_info[cell_ind] = row_index
                        cell_property_row_list.append(CellPropertyInfo(grid_span, 1, False))
                else:
                    cell_property_row_list.append(CellPropertyInfo(grid_span, 1, False))

                # split merged cells
                for span in range(grid_span - 1):
                    cell_property_row_list.append(CellPropertyInfo(1, 1, True))
                    cell_ind += 1
                    cells_text.append(cell_text)
                cell_ind += 1
                cells_text.append(cell_text)

            cell_property_list.append(cell_property_row_list)
            result_cells.append(cells_text)
            prev_row = cells_text

        return Table(cells=result_cells, metadata=TableMetadata(page_id=None, uid=self.uid), cells_properties=cell_property_list)

    def __get_cell_text(self, cell: Tag) -> str:
        cell_text = ""
        paragraphs = cell.find_all("w:p")

        for paragraph in paragraphs:
            for run_bs in paragraph.find_all("w:r"):
                run = Run(None, self.styles_extractor)
                run.get_text(run_bs)
                cell_text += run.text
            cell_text += '\n'

        if cell_text:
            cell_text = cell_text[:-1]  # remove \n in the end
        return cell_text
