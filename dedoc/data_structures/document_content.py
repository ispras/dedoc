from typing import List
from collections import OrderedDict

from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode


class DocumentContent:

    def __init__(self, tables: List[Table], structure: TreeNode):
        self.tables = tables
        self.structure = structure

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["structure"] = self.structure.to_dict()
        res["tables"] = [table.to_dict() for table in self.tables]
        return res

