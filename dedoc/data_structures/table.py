from typing import List

from dedoc.api.schema.table import Table as ApiTable
from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table_metadata import TableMetadata


class Table(Serializable):
    """
    This class holds information about tables in the document.
    We assume that a table has rectangle form (has the same number of columns in each row).
    Table representation is row-based i.e. external list contains list of rows.
    """
    def __init__(self, cells: List[List[CellWithMeta]], metadata: TableMetadata) -> None:
        """
        :param cells: a list of lists of cells (cell has text, colspan and rowspan attributes)
        :param metadata: some table metadata as location, size and so on
        """
        self.metadata = metadata
        self.cells = cells

    def to_api_schema(self) -> ApiTable:
        cells = [[cell.to_api_schema() for cell in row] for row in self.cells]
        return ApiTable(cells=cells, metadata=self.metadata.to_api_schema())
