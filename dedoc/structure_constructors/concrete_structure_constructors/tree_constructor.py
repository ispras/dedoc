from typing import List, Optional, Tuple

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructors.abstract_structure_constructor import AbstractStructureConstructor


class TreeConstructor(AbstractStructureConstructor):
    """
    This class is used to form a basic hierarchical document structure representation as a tree.

    The structure is built according to the lines' hierarchy levels and their types:
        - lines with hierarchy level (0, 0) are merged and become a root of the document;
        - lines with a type `list_item` become children of a new empty auxiliary node `list`;
        - each line is added as a separate tree node in the document hierarchy according to its hierarchy level:
            - if the level of the current line is less then the previous line level, the current line becomes its child;
            - else the line becomes a child of the first line which have less hierarchy level that the current line has.

    Hierarchy levels of the lines are compared lexicographically.

    **Example:**
        - **root line (0, 0)**
            - **first child line (1, 0)**
                - **line (2, 0)**
                    - **line (2, 1)**
                - **line (2, 0)**
            - **second child line (1, 0)**
    """

    def construct(self, document: UnstructuredDocument, parameters: Optional[dict] = None) -> ParsedDocument:
        """
        Build the tree structure representation for the given document intermediate representation.
        To get the information about the parameters look at the documentation of :class:`~dedoc.structure_constructors.AbstractStructureConstructor`.
        """
        document_name, not_document_name = self.__get_document_name(document.lines)
        not_document_name = self.__add_lists(not_document_name)
        tree = TreeNode.create(lines=document_name)
        for line in not_document_name:
            # add raw text line
            # multiline header
            hl_equal = line.metadata.hierarchy_level == tree.metadata.hierarchy_level
            line_type_equal = line.metadata.hierarchy_level.line_type == tree.metadata.hierarchy_level.line_type
            if line.metadata.hierarchy_level.can_be_multiline and hl_equal and line_type_equal:
                tree.add_text(line)
            # move up and add child

            else:
                while tree.metadata.hierarchy_level >= line.metadata.hierarchy_level:
                    tree = tree.parent
                tree = tree.add_child(line=line)
        tree = tree.get_root()
        tree.merge_annotations()
        document_content = DocumentContent(tables=document.tables, structure=tree)
        metadata = DocumentMetadata(**document.metadata)
        return ParsedDocument(content=document_content, metadata=metadata, warnings=document.warnings)

    def __get_document_name(self, lines: List[LineWithMeta]) -> Tuple[List[LineWithMeta], List[LineWithMeta]]:
        document_name = []
        other_lines = []
        for line in lines:
            if line.metadata.hierarchy_level.level_1 == 0 and line.metadata.hierarchy_level.level_2 == 0:
                document_name.append(line)
            else:
                other_lines.append(line)
        return document_name, other_lines

    def __add_lists(self, not_document_name: List[LineWithMeta]) -> List[LineWithMeta]:
        previous_hierarchy_levels = []
        res = []
        for line in not_document_name:
            if line.metadata.hierarchy_level.is_list_item():
                while len(previous_hierarchy_levels) > 0 and previous_hierarchy_levels[-1] > line.metadata.hierarchy_level:
                    previous_hierarchy_levels.pop()
                if previous_hierarchy_levels == [] or previous_hierarchy_levels[-1] < line.metadata.hierarchy_level:
                    list_line = self.__create_list_line(line)
                    res.append(list_line)
                    previous_hierarchy_levels.append(line.metadata.hierarchy_level)
            elif not line.metadata.hierarchy_level.is_raw_text():
                previous_hierarchy_levels = []
            res.append(line)
        return res

    @staticmethod
    def __create_list_line(line: LineWithMeta) -> LineWithMeta:
        hierarchy_level = HierarchyLevel(
            level_1=line.metadata.hierarchy_level.level_1,
            level_2=line.metadata.hierarchy_level.level_2 - 0.5,  # noqa  it is intentionaly for lists
            line_type="list",
            can_be_multiline=False
        )
        return LineWithMeta(line="",
                            metadata=LineMetadata(hierarchy_level=hierarchy_level, page_id=line.metadata.page_id, line_id=line.metadata.line_id),
                            annotations=[])
