import hashlib

from bs4 import Tag

from dedoc.data_structures import CellWithMeta, Table, TableMetadata
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.pptx_reader.properties_extractor import PropertiesExtractor
from dedoc.readers.pptx_reader.shape import PptxShape


class PptxTable:
    """
    This class corresponds to the table (tag <a:tbl>) in the slides xml files.
    """
    def __init__(self, xml: Tag, page_id: int, numbering_extractor: NumberingExtractor, properties_extractor: PropertiesExtractor) -> None:
        """
        Contains information about table properties.
        :param xml: BeautifulSoup tree with table properties
        """
        self.xml = xml
        self.page_id = page_id
        self.numbering_extractor = numbering_extractor
        self.properties_extractor = properties_extractor
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
        for tbl in self.xml.find_all("a:tbl"):
            tbl.extract()

        rows = self.xml.find_all("a:tr")
        cell_list = []

        for row in rows:
            cells = row.find_all("a:tc")
            col_index = 0
            cell_row_list = []

            for cell in cells:
                if int(cell.get("vMerge", 0)):  # vertical merge
                    cell_with_meta = CellWithMeta(lines=cell_list[-1][col_index].lines, colspan=1, rowspan=1, invisible=True)
                elif int(cell.get("hMerge", 0)):  # horizontal merge
                    cell_with_meta = CellWithMeta(lines=cell_row_list[-1].lines, colspan=1, rowspan=1, invisible=True)
                else:
                    colspan = int(cell.get("gridSpan", 1))  # gridSpan attribute describes number of horizontally merged cells
                    rowspan = int(cell.get("rowSpan", 1))  # rowSpan attribute for vertically merged set of cells (or horizontally split cells)
                    lines = PptxShape(xml=cell, page_id=self.page_id, numbering_extractor=self.numbering_extractor, init_line_id=0,
                                      properties_extractor=self.properties_extractor).get_lines()
                    cell_with_meta = CellWithMeta(lines=lines, colspan=colspan, rowspan=rowspan, invisible=False)

                cell_row_list.append(cell_with_meta)
                col_index += 1

            cell_list.append(cell_row_list)

        return Table(cells=cell_list, metadata=TableMetadata(page_id=self.page_id, uid=self.uid))
