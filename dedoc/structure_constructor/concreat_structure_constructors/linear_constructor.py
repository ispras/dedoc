from typing import Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructor.concreat_structure_constructors.abstract_structure_constructor import AbstractStructureConstructor


class LinearConstructor(AbstractStructureConstructor):

    def __init__(self):
        pass

    def structure_document(self,
                           document: UnstructuredDocument,
                           structure_type: Optional[str] = None) -> DocumentContent:
        lines = document.lines
        tree = TreeNode.create(lines=[])
        for line in lines:
            tree.add_child(line)
        tree.merge_annotations()
        return DocumentContent(tables=document.tables, structure=tree)
