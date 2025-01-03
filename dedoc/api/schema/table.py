from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.cell_with_meta import CellWithMeta
from dedoc.api.schema.table_metadata import TableMetadata


class Table(BaseModel):
    """
    Holds information about tables in the document.
    We assume that a table has rectangle form (has the same number of columns in each row).
    Table representation is row-based i.e. external list contains list of rows.

    :ivar metadata: a list of lists of table cells (cell has text lines, colspan and rowspan attributes)
    :ivar cells: table metadata as location, title and so on

    :vartype metadata: TableMetadata
    :vartype cells: List[List[CellWithMeta]]
    """
    cells: List[List[CellWithMeta]] = Field(description="List of lists of table cells (cell has text, colspan and rowspan attributes)")
    metadata: TableMetadata = Field(description="Table meta information")
