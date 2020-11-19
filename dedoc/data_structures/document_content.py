from typing import List
from collections import OrderedDict

from flask_restplus import fields, Api, Model

from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode


class DocumentContent(Serializable):

    def __init__(self, tables: List[Table], structure: 'TreeNode'):
        """
        That class holds the document content - structured text and tables
        :param tables: list of document tables
        :param structure: Tree structure in which content of the document is organized
        """
        self.tables = tables
        self.structure = structure

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["structure"] = self.structure.to_dict()
        res["tables"] = [table.to_dict() for table in self.tables]
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('DocumentContent', {
            'structure': fields.Nested(TreeNode.get_api_dict(api),
                                       readonly=True,
                                       description='document content structure'),
            'tables': fields.List(fields.Nested(Table.get_api_dict(api), description="tables structure"))
        })
