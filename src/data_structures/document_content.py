from collections import OrderedDict
from typing import List

from flask_restx import fields, Api, Model

from src.data_structures.serializable import Serializable
from src.data_structures.table import Table
from src.data_structures.tree_node import TreeNode


class DocumentContent(Serializable):

    def __init__(self, tables: List[Table], structure: 'TreeNode', warnings: List[str] = None) -> None:
        """
        That class holds the document content - structured text and tables
        :param tables: list of document tables
        :param structure: Tree structure in which content of the document is organized
        :param warnings: list of warnings, obtained in the process of the document structure constructing
        """
        self.tables = tables
        self.structure = structure
        self.warnings = warnings if warnings is not None else []

    def to_dict(self, old_version: bool) -> dict:
        res = OrderedDict()
        res["structure"] = self.structure.to_dict(old_version)
        res["tables"] = [table.to_dict(old_version) for table in self.tables]
        return res

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('DocumentContent', {
            'structure': fields.Nested(TreeNode.get_api_dict(api),
                                       readonly=True,
                                       description='document content structure'),
            'tables': fields.List(fields.Nested(Table.get_api_dict(api), description="tables structure"))
        })
