from collections import OrderedDict
from typing import List

from flask_restplus import fields, Api, Model

from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table_metadata import TableMetadata


class Table(Serializable):

    def __init__(self, cells: List[List[str]], metadata: TableMetadata):
        """
        That class holds information about tables in the document. We assume that a table has rectangle form
        (has the same number of columns in each row)
        :param cells: a list of list of cells (cell is string). Table representation is row-based e.q. external list
        contains list of rows.
        :param metadata: some table metadata, as location, size and so on.
        """
        self.cells = cells
        self.metadata = metadata

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["cells"] = self.cells
        res["metadata"] = self.metadata.to_dict()
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('Table', {
            'cells': fields.List(fields.List(fields.String(description="Cell contains text")),
                                 description="matrix of cells"),
            'metadata': fields.Nested(TableMetadata.get_api_dict(api),
                                      readonly=True,
                                      description='Table meta information')
        })


