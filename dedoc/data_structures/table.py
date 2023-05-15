from collections import OrderedDict
from typing import List, Optional, Any
from flask_restx import fields, Api, Model

from dedoc.data_structures.cell_property import CellProperty
from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table_metadata import TableMetadata


class Table(Serializable):
    """
    This class holds information about tables in the document.
    We assume that a table has rectangle form (has the same number of columns in each row).
    Table representation is row-based i.e. external list contains list of rows.
    """
    def __init__(self, cells: List[List[str]], metadata: TableMetadata, cells_properties: Optional[List[List[Optional[Any]]]] = None) -> None:
        """
        :param cells: a list of lists of cells (cell has text, colspan and rowspan attributes).
        :param metadata: some table metadata, as location, size and so on.
        :param cells_properties: a list of lists of cells properties - each should contain attributes rowspan, colspan, invisible (for repeated cells)
        """
        self.cells = [[cell_text for cell_text in row] for row in cells]
        metadata.cell_properties = [[CellProperty(cell) for cell in row] for row in cells_properties] if cells_properties else None
        self.metadata = metadata

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["cells"] = [[cell_text for cell_text in row] for row in self.cells]
        res["metadata"] = self.metadata.to_dict()
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('Table', {
            'cells': fields.List(fields.List(fields.String(description="Cell contains text")), description="matrix of cells"),
            'metadata': fields.Nested(TableMetadata.get_api_dict(api), readonly=True, description='Table meta information')
        })
