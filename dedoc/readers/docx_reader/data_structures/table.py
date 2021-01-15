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
        result_cells = []
        rows = self.xml.find_all("w:tr")
        for row in rows:
            cells = row.find_all("w:tc")
            cells_text = []
            for cell in cells:
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
                cells_text.append(cell_text)
            result_cells.append(cells_text)

        return result_cells
