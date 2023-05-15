from typing import List, Optional

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table


class UnstructuredDocument:
    """
    This class holds information about raw document content: its text, tables and attachments, that have been procured using one of the readers.
    Text is represented as a flat list of lines, hierarchy level of each line isn't defined (only tag hierarchy level may exist).
    """
    def __init__(self,
                 tables: List[Table],
                 lines: List[LineWithMeta],
                 attachments: List[AttachedFile],
                 warnings: List[str] = None,
                 metadata: Optional[dict] = None) -> None:
        """
        :param tables: list of document tables
        :param lines: list of raw document lines
        :param attachments: list of documents attachments
        :param warnings: list of warnings, obtained in the process of the document parsing
        :param metadata: additional data
        """
        self.tables = tables
        self.lines = lines
        self.attachments = attachments
        self.warnings = warnings if warnings else []
        self.metadata = metadata if metadata is not None else {}
