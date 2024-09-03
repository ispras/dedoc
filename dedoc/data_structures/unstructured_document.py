from typing import List, Optional

from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table


class UnstructuredDocument:
    """
    This class holds information about raw document content: its text, tables and attachments, that have been procured using one of the readers.
    Text is represented as a flat list of lines, hierarchy level of each line isn't defined (only tag hierarchy level may exist).

    :ivar lines: list of textual lines with metadata returned by a reader
    :ivar tables: list of document tables returned by a reader
    :ivar attachments: list of document attached files
    :ivar metadata: information about the document (like in :class:`~dedoc.data_structures.DocumentMetadata`)
    :ivar warnings: list of warnings, obtained in the process of the document parsing

    :vartype lines: List[LineWithMeta]
    :vartype tables: List[Table]
    :vartype attachments: List[AttachedFile]
    :vartype metadata: dict
    :vartype warnings: List[str]
    """
    def __init__(self,
                 tables: List[Table],
                 lines: List[LineWithMeta],
                 attachments: List[AttachedFile],
                 warnings: Optional[List[str]] = None,
                 metadata: Optional[dict] = None) -> None:
        """
        :param tables: list of document tables
        :param lines: list of raw document lines
        :param attachments: list of documents attachments
        :param warnings: list of warnings, obtained in the process of the document parsing
        :param metadata: additional data
        """
        self.tables: List[Table] = tables
        self.lines: List[LineWithMeta] = lines
        self.attachments: List[AttachedFile] = attachments
        self.warnings: List[str] = warnings if warnings else []
        self.metadata: dict = metadata if metadata is not None else {}

    def get_text(self) -> str:
        return LineWithMeta.join(self.lines).line
