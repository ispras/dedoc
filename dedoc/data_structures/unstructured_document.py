from typing import List

from dedoc.data_structures.table import Table
from dedoc.data_structures.line_with_meta import LineWithMeta


class UnstructuredDocument:

    def __init__(self, tables: List[Table], lines: List[LineWithMeta]):
        self.tables = tables
        self.lines = lines
