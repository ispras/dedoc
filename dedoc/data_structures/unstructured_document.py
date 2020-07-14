from typing import List

from dedoc.data_structures.table import Table
from dedoc.data_structures.line_with_meta import LineWithMeta


class UnstructuredDocument:

    def __init__(self, tables: List[Table], lines: List[LineWithMeta]):
        """
        That class hold information about document content: its text and tables. Text is represented as flat list of lines.
        :param tables: list of document tables
        :param lines: list of document lines
        """
        self.tables = tables
        self.lines = lines
