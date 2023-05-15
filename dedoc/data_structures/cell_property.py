from collections import OrderedDict
from typing import Any

from flask_restx import fields, Api, Model
import numpy as np

from dedoc.data_structures.serializable import Serializable


class CellProperty(Serializable):
    """
    This class holds information about the table cell.
    """
    def __init__(self, cell: Any) -> None:
        """
        :param cell: class which should contain the following attributes: colspan, rowspan, invisible.
        """
        self.colspan = cell.colspan
        self.rowspan = cell.rowspan
        self.invisible = cell.invisible

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["colspan"] = int(np.int8(self.colspan))
        res["rowspan"] = int(np.int8(self.rowspan))
        res["invisible"] = self.invisible
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('CellProperty', {
            'colspan': fields.Integer(description='attribute of union column count'),
            'rowspan': fields.Integer(description='attribute of union row count'),
            'invisible': fields.Boolean(description='flag for cell display (for example: if invisible==true then style=\"display: none\")'),
        })
