import copy
from collections import OrderedDict
from typing import Any, List

import numpy as np
from dedocutils.data_structures import BBox

from dedoc.data_structures import CellWithMeta, Table, TableMetadata
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.location import Location


class ScanTable:
    def __init__(self, page_number: int, matrix_cells: List[List[Cell]] = None, bbox: BBox = None, name: str = "", order: int = -1) -> None:
        self.matrix_cells = matrix_cells
        self.page_number = page_number
        self.locations = []
        self.name = name
        self.order = order
        if bbox is not None:
            self.locations.append(Location(page_number, bbox))

    def extended(self, table: "ScanTable") -> None:
        # extend locations
        self.locations.extend(table.locations)
        # extend values
        self.matrix_cells.extend(table.matrix_cells)
        # extend order
        self.order = max(self.order, table.order)

    def to_table(self) -> Table:
        metadata = TableMetadata(page_id=self.page_number, uid=self.name, rotated_angle=self.location.rotated_angle)
        cells_with_meta = [[CellWithMeta.create_from_cell(cell) for cell in row] for row in self.matrix_cells]
        return Table(metadata=metadata, cells=cells_with_meta)

    @staticmethod
    def get_cells_text(attr_cells: List[List[Cell]]) -> List[List[str]]:
        attrs = []
        for i in range(0, len(attr_cells)):
            attrs.append([a.get_text() for a in attr_cells[i]])

        return attrs

    @staticmethod
    def get_key_value_attrs(attrs: List, val: Any) -> dict:  # noqa
        res_attrs = []
        for i in range(0, len(attrs)):
            res_attrs.append({"attr": attrs[i]})
        res = {
            "attrs": res_attrs,
            "val": val
        }
        return res

    @staticmethod
    def get_index_of_end_string_attr(matrix_cells: List[List[Cell]]) -> int:
        end_attr_string = 0
        for i in range(0, len(matrix_cells)):
            if matrix_cells[i][0].is_attribute:
                end_attr_string = i

        return end_attr_string

    @staticmethod
    def get_attributes_cell(matrix_cells: List[List[Cell]]) -> (List[int], List[List[Cell]], int):
        required_columns = []
        for j in range(0, len(matrix_cells[0])):
            if matrix_cells[0][j].is_attribute_required:
                required_columns.append(j)

        end_attr_string = ScanTable.get_index_of_end_string_attr(matrix_cells)

        attrs = copy.deepcopy(np.array(matrix_cells[0:end_attr_string + 1]))
        attrs = attrs.transpose().tolist()

        return [required_columns, attrs, end_attr_string]

    @staticmethod
    def get_matrix_attrs_and_data(matrix_cells: List[List[Cell]]) -> (List[List[Cell]], List[List[str]], List[List[str]]):
        required_columns, attrs, end_attr_string = ScanTable.get_attributes_cell(matrix_cells)
        attrs_text = ScanTable.get_cells_text(attrs)

        data = matrix_cells[(end_attr_string + 1):]
        data_text = ScanTable.get_cells_text(data)

        return [attrs, attrs_text, data_text]

    @property
    def location(self) -> Location:
        return min(self.locations)

    @property
    def uid(self) -> str:
        return self.name

    def to_dict(self) -> dict:
        data_text = ScanTable.get_cells_text(self.matrix_cells)

        res = OrderedDict()
        res["locations"] = [location.to_dict() for location in self.locations]
        res["cells"] = data_text

        return res
