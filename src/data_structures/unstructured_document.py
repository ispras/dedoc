from typing import List, Optional

from src.data_structures.attached_file import AttachedFile
from src.data_structures.line_with_meta import LineWithMeta
from src.data_structures.table import Table


class UnstructuredDocument:

    def __init__(self,
                 tables: List[Table],
                 lines: List[LineWithMeta],
                 attachments: List[AttachedFile],
                 warnings: List[str] = None,
                 metadata: Optional[dict] = None) -> None:
        """
        That class holds information about document content: its text and tables. Text is represented as flat
        list of lines.
        :param tables: list of document tables
        :param lines: list of document lines
        :param warnings: list of warnings, obtained in the process of the document parsing
        :param metadata: additional data
        """
        self.tables = tables
        self.lines = lines
        self.attachments = attachments
        self.warnings = warnings if warnings else []
        self.metadata = metadata if metadata is not None else {}
