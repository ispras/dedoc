from typing import List, Optional

from dedoc.api.schema.document_content import DocumentContent as ApiDocumentContent
from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode


class DocumentContent(Serializable):
    """
    This class holds the document content - structured text and tables.

    :ivar tables: list of document tables
    :ivar structure: tree structure of the document nodes with text and additional metadata
    :ivar warnings: list of warnings, obtained in the process of the document parsing

    :vartype tables: List[Table]
    :vartype structure: TreeNode
    :vartype warnings: List[str]
    """
    def __init__(self, tables: List[Table], structure: TreeNode, warnings: Optional[List[str]] = None) -> None:
        """
        :param tables: list of document tables
        :param structure: tree structure in which content of the document is organized
        :param warnings: list of warnings
        """
        self.tables: List[Table] = tables
        self.structure: TreeNode = structure
        self.warnings: List[str] = warnings if warnings is not None else []

    def to_api_schema(self) -> ApiDocumentContent:
        structure = self.structure.to_api_schema()
        tables = [table.to_api_schema() for table in self.tables]
        return ApiDocumentContent(structure=structure, tables=tables)
