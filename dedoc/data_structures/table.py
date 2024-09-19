from typing import List

from dedoc.api.schema.table import Table as ApiTable
from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table_metadata import TableMetadata


class Table(Serializable):
    """
    This class holds information about tables in the document.
    We assume that a table has rectangle form (has the same number of columns in each row).
    If some cells are merged, they are duplicated and information about merge is stored in rowspan and colspan.
    Table representation is row-based i.e. external list contains list of rows.

    :ivar metadata: a list of lists of table cells (cell has text lines, colspan and rowspan attributes)
    :ivar cells: table metadata as location, title and so on

    :vartype metadata: TableMetadata
    :vartype cells: List[List[CellWithMeta]]
    """
    def __init__(self, cells: List[List[CellWithMeta]], metadata: TableMetadata) -> None:
        """
        :param cells: a list of lists of cells
        :param metadata: table metadata
        """
        self.metadata: TableMetadata = metadata
        self.cells: List[List[CellWithMeta]] = cells

    def to_api_schema(self) -> ApiTable:
        cells = [[cell.to_api_schema() for cell in row] for row in self.cells]
        return ApiTable(cells=cells, metadata=self.metadata.to_api_schema())
