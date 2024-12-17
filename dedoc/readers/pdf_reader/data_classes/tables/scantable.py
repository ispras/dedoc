from typing import List

from dedocutils.data_structures import BBox

from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.location import Location


class ScanTable(Table):
    def __init__(self, page_number: int, cells: List[List[CellWithMeta]], bbox: BBox, order: int = -1) -> None:

        super().__init__(cells, TableMetadata(page_id=page_number))
        self.order = order
        self.locations = [Location(page_number, bbox)]

    def extended(self, table: "ScanTable") -> None:
        # extend locations
        self.locations.extend(table.locations)
        # extend values
        self.cells.extend(table.cells)
        # extend order
        self.order = max(self.order, table.order)

    def check_on_cell_instance(self) -> bool:
        if len(self.cells) == 0:
            return False
        if len(self.cells[0]) == 0:
            return False
        if not isinstance(self.cells[0][0], Cell):
            return False
        return True

    def __get_cells_text(self, cells: List[List[CellWithMeta]]) -> List[List[str]]:
        return [[cell.get_text() for cell in row] for row in cells]

    @property
    def location(self) -> Location:
        return min(self.locations)

    @property
    def uid(self) -> str:
        return self.metadata.uid

    def to_dict(self) -> dict:
        from collections import OrderedDict

        data_text = self.__get_cells_text(self.cells)

        res = OrderedDict()
        res["locations"] = [location.to_dict() for location in self.locations]
        res["cells"] = data_text

        return res
