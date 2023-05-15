from typing import Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructors.abstract_structure_constructor import AbstractStructureConstructor


class LinearConstructor(AbstractStructureConstructor):

    def __init__(self) -> None:
        pass

    def structure_document(self, document: UnstructuredDocument, version: str, structure_type: Optional[str] = None) -> ParsedDocument:
        lines = document.lines
        tree = TreeNode.create(lines=[])
        for line in lines:
            tree.add_child(line)
        tree.merge_annotations()
        document_content = DocumentContent(tables=document.tables, structure=tree)
        metadata = DocumentMetadata(**document.metadata)
        return ParsedDocument(content=document_content, metadata=metadata, version=version)
