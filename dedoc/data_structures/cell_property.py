from collections import OrderedDict

import numpy as np
from flask_restx import Api, Model, fields

from dedoc.data_structures import Annotation
from dedoc.data_structures.serializable import Serializable
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell


class CellProperty(Serializable):
    """
    This class holds information about the table cell.
    """
    def __init__(self, colspan: int, rowspan: int, invisible: bool, annotations: List[Annotation]) -> None:  # noqa
        """
        :param cell: class which should contain the following attributes: colspan, rowspan, invisible.
        """
        self.colspan = colspan
        self.rowspan = rowspan
        self.invisible = invisible
        self.annotations = annotations

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["annotations"] = [annotation.to_dict() for annotation in self.annotations]
        res["colspan"] = int(np.int8(self.colspan))
        res["rowspan"] = int(np.int8(self.rowspan))
        res["invisible"] = self.invisible
        return res

    @staticmethod
    def get_cell_property_from_cell(cell: Cell) -> "CellProperty":
        return CellProperty(colspan=cell.colspan, rowspan=cell.rowspan, invisible=cell.invisible, annotations=cell.get_annotations())

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model("CellProperty", {
            "colspan": fields.Integer(description="attribute of union column count"),
            "rowspan": fields.Integer(description="attribute of union row count"),
            "invisible": fields.Boolean(description='flag for cell display (for example: if invisible==true then style="display: none")'),
            "annotations": fields.List(
                fields.Nested(Annotation.get_api_dict(api), description="Text annotations (font, size, bold, italic and etc)")),
        })
