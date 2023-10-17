from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.line_with_meta import LineWithMeta


class CellWithMeta(BaseModel):
    """
    Holds the information about the cell: list of lines and cell properties (rowspan, colspan, invisible).
    """
    lines: List[LineWithMeta] = Field(description="Textual lines of the cell with annotations")
    rowspan: int = Field(description="Number of rows to span like in HTML format", example=1)
    colspan: int = Field(description="Number of columns to span like in HTML format", example=2)
    invisible: bool = Field(description="Indicator for displaying or hiding cell text", example=False)
