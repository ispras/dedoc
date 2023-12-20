from typing import Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructors.abstract_structure_constructor import AbstractStructureConstructor


class LinearConstructor(AbstractStructureConstructor):
    """
    This class is used to form a simple basic document structure representation as a list of document lines.
    The result contains the empty root node with the consecutive list of all document lines as its children.
    """

    def construct(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> ParsedDocument:
        """
        Build the linear structure representation for the given document intermediate representation.
        To get the information about the parameters look at the documentation of :class:`~dedoc.structure_constructors.AbstractStructureConstructor`.
        """
        lines = document.lines
        tree = TreeNode.create(lines=[])
        for line in lines:
            tree.add_child(line)
        tree.merge_annotations()
        document_content = DocumentContent(tables=document.tables, structure=tree)
        metadata = DocumentMetadata(**document.metadata)
        return ParsedDocument(content=document_content, metadata=metadata, warnings=document.warnings)
