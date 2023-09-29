from collections import OrderedDict
from typing import List

import numpy as np
from flask_restx import Api, Model, fields

from dedoc.data_structures import Annotation
from dedoc.data_structures.line_with_meta import LineWithMeta


class CellWithMeta:
    """
    This class holds the information about the cell: list of lines and cell properties (rowspan, colspan, invisible).
    """
    def __init__(self, lines: List[LineWithMeta], colspan: int = 1, rowspan: int = 1, invisible: bool = False) -> None:
        """
        :param lines: textual lines of the cell
        :param colspan: number of columns to span like in HTML format
        :param rowspan: number of rows to span like in HTML format
        :param invisible: indicator for displaying or hiding cell text
        """
        self.lines = lines
        self.colspan = colspan
        self.rowspan = rowspan
        self.invisible = invisible

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
    def create_from_cell(cell: "Cell") -> "CellWithMeta": # noqa
        return CellWithMeta(lines=cell.lines, colspan=cell.colspan, rowspan=cell.rowspan, invisible=cell.invisible)

    def to_dict(self) -> dict:
        res = OrderedDict()

        res["lines"] = [line.to_dict() for line in self.lines]
        res["colspan"] = int(np.int8(self.colspan))
        res["rowspan"] = int(np.int8(self.rowspan))
        res["invisible"] = self.invisible
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model("CellWithMeta", {
            "colspan": fields.Integer(description="attribute of union column count"),
            "rowspan": fields.Integer(description="attribute of union row count"),
            "invisible": fields.Boolean(description='flag for cell display (for example: if invisible==true then style="display: none")'),
            "lines": fields.List(fields.Nested(LineWithMeta.get_api_dict(api), description="Text annotations (font, size, bold, italic and etc)")),
        })
