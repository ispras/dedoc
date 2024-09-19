from typing import List

from pydantic import BaseModel, Field

from dedoc.api.schema.annotation import Annotation
from dedoc.api.schema.line_metadata import LineMetadata


class TreeNode(BaseModel):
    """
    Helps to represent document as recursive tree structure.
    It has list of children `TreeNode` nodes (empty list for a leaf node).

    :ivar node_id: unique node identifier
    :ivar text: text of the node (may contain several lines)
    :ivar annotations: some metadata related to the part of the text (as font size)
    :ivar metadata: metadata refers to entire node (as node type)
    :ivar subparagraphs: list of child of this node

    :vartype node_id: str
    :vartype text: str
    :vartype annotations: List[Annotation]
    :vartype metadata: LineMetadata
    :vartype subparagraphs: List[TreeNode]
    """
    node_id: str = Field(description="Document element identifier. It is unique within a document content tree. "
                                     "The identifier consists of numbers separated by dots where each number "
                                     "means node's number among nodes with the same level in the document hierarchy.)", example="0.2.1")
    text: str = Field(description="Text of the node", example="Some text")
    annotations: List[Annotation] = Field(description="Some metadata related to the part of the text (as font size)")
    metadata: LineMetadata = Field(description="Metadata for the entire node (as node type)")
    subparagraphs: List["TreeNode"] = Field(description="List of children of this node, each child is `TreeNode`")
