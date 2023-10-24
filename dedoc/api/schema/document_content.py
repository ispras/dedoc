from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.table import Table
from dedoc.api.schema.tree_node import TreeNode


class DocumentContent(BaseModel):
    """
    Content of the document - structured text and tables.
    """
    structure: TreeNode = Field(description="Tree structure where content of the document is organized")
    tables: List[Table] = Field(description="List of document tables")
