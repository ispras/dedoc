from collections import OrderedDict
from typing import List

from dedoc.data_structures.table_metadata import TableMetadata


class Table:

    def __init__(self, cells: List[List[str]], metadata: TableMetadata):
        self.cells = cells
        self.metadata = metadata

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["cells"] = self.cells
        res["metadata"] = self.metadata.to_dict()
        return res
