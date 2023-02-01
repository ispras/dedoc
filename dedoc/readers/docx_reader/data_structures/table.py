import hashlib
from types import SimpleNamespace
from typing import List, Tuple
from bs4 import BeautifulSoup

from dedoc.readers.docx_reader.data_structures.run import Run
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor


class DocxTable:
    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor: StylesExtractor) -> None:
        """
        contains information about table properties
        :param xml: BeautifulSoup tree with table properties
        """
        self.xml = xml
        self._uid = hashlib.md5(xml.encode()).hexdigest()
        self.styles_extractor = styles_extractor

    @property
    def uid(self) -> str:
        return self._uid

    def get_cells(self) -> Tuple[List[List[str]], List[List[SimpleNamespace]]]:
        """
        returns list of lists with table cells
        merged cells are split and duplicated in result table
        """
        # tbl tag defines table
        # tr tag defines table row
        # tc tag defines table cell
        result_cells = []

        # delete tables inside tables
        for tbl in self.xml.find_all("w:tbl"):
            tbl.extract()

        rows = self.xml.find_all("w:tr")
        prev_row = []

        cell_property_list = []
        for row in rows:
            cells = row.find_all("w:tc")
            cells_text = []

            cell_ind = 0
            cell_property_row_list = []
            for cell in cells:
                cell_property_info = {}
                # gridSpan tag describes number of horizontally merged cells
                if cell.gridSpan:
                    grid_span = int(cell.gridSpan["w:val"])
                else:
                    grid_span = 1
                cell_property_info["colspan"] = grid_span
                # get text of the cell
                cell_text = self.__get_cell_text(cell)
                # vmerge tag for vertically merged set of cells (or horizontally split cells)
                # attribute val may be "restart" or "continue" ("continue" if omitted)
                invisible_flag = False
                if cell.vMerge:
                    value = cell.vMerge.get("w:val", "continue")
                    if value == "continue":
                        invisible_flag = True
                        cell_text += prev_row[cell_ind]
                    cell_property_info["rowspan"] = 0
                else:
                    cell_property_info["rowspan"] = 1
                cell_property_info["invisible"] = invisible_flag
                # split merged cells
                cell_property_row_list.append(SimpleNamespace(**cell_property_info))
                cell_property_info = {}
                for span in range(grid_span - 1):
                    cell_property_info["colspan"] = 1
                    cell_property_info["rowspan"] = 1
                    cell_property_info["invisible"] = True
                    cell_property_row_list.append(SimpleNamespace(**cell_property_info))
                    cell_ind += 1
                    cells_text.append(cell_text)
                cell_ind += 1
                cells_text.append(cell_text)
            cell_property_list.append(cell_property_row_list)
            result_cells.append(cells_text)
            prev_row = cells_text
        cell_property_list = self.__corrected_rowspan_list(cell_property_list)
        return result_cells, cell_property_list

    def __get_cell_text(self, cell: BeautifulSoup) -> str:
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

    @staticmethod
    def __corrected_rowspan_list(cell_property_list: List[List[SimpleNamespace]]) -> List[List[SimpleNamespace]]:
        for col_index in range(len(cell_property_list[0])):
            rowspan_start_index = 0
            rowspan_count = 0
            for row_index, row in enumerate(cell_property_list):
                cell = cell_property_list[row_index][col_index]
                if cell.rowspan == 0:
                    rowspan_count += 1
                    if cell.invisible is False:
                        rowspan_start_index = row_index
                    elif cell.invisible is True:
                        cell.rowspan = 1
            if rowspan_count != 0:
                cell_property_list[rowspan_start_index][col_index].rowspan = rowspan_count
        return cell_property_list
