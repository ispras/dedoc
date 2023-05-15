from collections import OrderedDict
from typing import Any

from flask_restx import fields, Api, Model
import numpy as np

from dedoc.data_structures.serializable import Serializable


class CellProperty(Serializable):
    def __init__(self, cell: Any) -> None:
        """
        That class holds information about table cell.
        :param cell: a cell class.
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
