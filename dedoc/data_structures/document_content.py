from typing import List

from dedoc.api.schema.document_content import DocumentContent as ApiDocumentContent
from dedoc.data_structures.serializable import Serializable
from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode


class DocumentContent(Serializable):
    """
    This class holds the document content - structured text and tables.
    """
    def __init__(self, tables: List[Table], structure: TreeNode, warnings: List[str] = None) -> None:
        """
        :param tables: list of document tables
        :param structure: tree structure in which content of the document is organized
        :param warnings: list of warnings, obtained in the process of the document structure constructing
        """
        self.tables = tables
        self.structure = structure
        self.warnings = warnings if warnings is not None else []

    def to_api_schema(self) -> ApiDocumentContent:
        structure = self.structure.to_api_schema()
        tables = [table.to_api_schema() for table in self.tables]
        return ApiDocumentContent(structure=structure, tables=tables)
