from typing import List, Tuple, Optional

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_constructors.abstract_structure_constructor import AbstractStructureConstructor
from dedoc.data_structures.hierarchy_level import HierarchyLevel


class TreeConstructor(AbstractStructureConstructor):

    def __init__(self) -> None:
        pass

    def structure_document(self, document: UnstructuredDocument, version: str, structure_type: Optional[str] = None) -> ParsedDocument:
        document_name, not_document_name = self.__get_document_name(document.lines)
        not_document_name = self.__add_lists(not_document_name)
        tree = TreeNode.create(lines=document_name)
        for line in not_document_name:
            # add raw text line
            # multiline header
            if (line.metadata.hierarchy_level.can_be_multiline and
                    line.metadata.hierarchy_level == tree.metadata.hierarchy_level and
                    line.metadata.hierarchy_level.line_type == tree.metadata.hierarchy_level.line_type):
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
        return ParsedDocument(content=document_content, metadata=metadata, version=version)

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
