from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.table import Table
from dedoc.api.schema.tree_node import TreeNode


class DocumentContent(BaseModel):
    """
    Content of the document - structured text and tables.

    :ivar tables: list of document tables
    :ivar structure: tree structure of the document nodes with text and additional metadata

    :vartype tables: List[Table]
    :vartype structure: TreeNode
    """
    structure: TreeNode = Field(description="Tree structure where content of the document is organized")
    tables: List[Table] = Field(description="List of document tables")
