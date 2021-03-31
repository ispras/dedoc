import hashlib
from typing import List

from bs4 import BeautifulSoup

from dedoc.readers.docx_reader.data_structures.run import Run


class DocxTable:
    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor: "StylesExtractor") -> None:
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

    def get_cells(self) -> List[List[str]]:
        """
        returns list of lists with table cells
        merged cells are split and duplicated in result table
        """
        # tbl tag defines table
        # tr tag defines table row
        # tc tag defines table cell
        result_cells = []

        rows = self.xml.find_all("w:tr")
        prev_row = []
        for row in rows:
            cells = row.find_all("w:tc")
            cells_text = []

            cell_ind = 0
            for cell in cells:
                # gridSpan tag describes number of horizontally merged cells
                if cell.gridSpan:
                    grid_span = int(cell.gridSpan["w:val"])
                else:
                    grid_span = 1
                # get text of the cell
                cell_text = self.__get_cell_text(cell)
                # vmerge tag for vertically merged set of cells (or horizontally split cells)
                # attribute val may be "restart" or "continue" ("continue" if omitted)
                if cell.vMerge:
                    try:
                        value = cell.vMerge["w:val"]
                    except KeyError:
                        value = "continue"
                    if value == "continue":
                        try:
                            cell_text += prev_row[cell_ind]
                        except IndexError:
                            pass
                # split merged cells
                for span in range(grid_span):
                    cell_ind += 1
                    cells_text.append(cell_text)

            result_cells.append(cells_text)
            prev_row = cells_text

        return result_cells

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
