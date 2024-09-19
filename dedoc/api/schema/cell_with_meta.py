from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.line_with_meta import LineWithMeta


class CellWithMeta(BaseModel):
    """
    Holds the information about the cell: list of lines and cell properties (rowspan, colspan, invisible).

    :ivar lines: list of textual lines of the cell
    :ivar colspan: number of columns to span (for cells merged horizontally)
    :ivar rowspan: number of rows to span (for cells merged vertically)
    :ivar invisible: indicator for displaying or hiding cell text - cells that are merged with others are hidden (for HTML display)

    :vartype lines: List[LineWithMeta]
    :vartype colspan: int
    :vartype rowspan: int
    :vartype invisible: bool
    """
    lines: List[LineWithMeta] = Field(description="Textual lines of the cell with annotations")
    rowspan: int = Field(description="Number of rows to span like in HTML format", example=1)
    colspan: int = Field(description="Number of columns to span like in HTML format", example=2)
    invisible: bool = Field(description="Indicator for displaying or hiding cell text", example=False)
