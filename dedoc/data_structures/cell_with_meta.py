from typing import List

from dedoc.api.schema.cell_with_meta import CellWithMeta as ApiCellWithMeta
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.serializable import Serializable


class CellWithMeta(Serializable):
    """
    This class holds the information about the cell: list of lines and cell properties (rowspan, colspan, invisible).

    :ivar lines: list of textual lines of the cell
    :ivar colspan: number of columns to span (for cells merged horizontally)
    :ivar rowspan: number of rows to span (for cells merged vertically)
    :ivar invisible: indicator for displaying or hiding cell text - cells that are merged with others are hidden (for HTML display)

    :vartype lines: List[LineWithMeta]
    :vartype colspan: int
    :vartype rowspan: int
    :vartype invisible: bool
    """
    def __init__(self, lines: List[LineWithMeta], colspan: int = 1, rowspan: int = 1, invisible: bool = False) -> None:
        """
        :param lines: textual lines of the cell
        :param colspan: number of columns to span like in HTML format
        :param rowspan: number of rows to span like in HTML format
        :param invisible: indicator for displaying or hiding cell text
        """
        self.lines: List[LineWithMeta] = lines
        self.colspan: int = colspan
        self.rowspan: int = rowspan
        self.invisible: bool = invisible

    def __repr__(self) -> str:
        return f"CellWithMeta({self.get_text()[:65]})"

    def get_text(self) -> str:
        """
        Get merged text of all cell lines
        """
        return "\n".join([line.line for line in self.lines])

    def get_annotations(self) -> List[Annotation]:
        """
        Get merged annotations of all cell lines (start/end of annotations moved according to the merged text)
        """
        return LineWithMeta.join(lines=self.lines, delimiter="\n").annotations

    @staticmethod
    def create_from_cell(cell: "CellWithMeta") -> "CellWithMeta":
        return CellWithMeta(lines=cell.lines, colspan=cell.colspan, rowspan=cell.rowspan, invisible=cell.invisible)

    def to_api_schema(self) -> ApiCellWithMeta:
        import numpy as np

        lines = [line.to_api_schema() for line in self.lines]
        return ApiCellWithMeta(lines=lines, colspan=int(np.int8(self.colspan)), rowspan=int(np.int8(self.rowspan)), invisible=self.invisible)
