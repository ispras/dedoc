from typing import List, Tuple

from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.tree_node import TreeNode
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.manager_config import get_manager_config
from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta


class TreeConstructor:

    def __init__(self):
        pass

    def construct_tree(self, document: UnstructuredDocument) -> DocumentContent:
        """

        :param document: document with linear structure
        :return:
        """
        lines = document.lines
        document_name, not_document_name = self.__get_document_name(lines)
        not_document_name = self.__add_lists(not_document_name)
        tree = TreeNode.create(texts=[line.line for line in document_name])
        for line in not_document_name:
            # add raw text line
            if line.hierarchy_level.is_raw_text():
                if tree.hierarchy_level.is_raw_text():
                    tree.add_text(line)
                else:
                    tree = tree.add_child(line)
            # multiline header
            elif (line.hierarchy_level.can_be_multiline and
                  line.hierarchy_level == tree.hierarchy_level and
                  line.hierarchy_level.paragraph_type == tree.hierarchy_level.paragraph_type
            ):
                tree.add_text(line)
            # move up and add child

            else:
                while tree.hierarchy_level >= line.hierarchy_level:
                    tree = tree.parent
                tree = tree.add_child(line=line)
        tree = tree.get_root()
        return DocumentContent(tables=document.tables, structure=tree)

    def __get_document_name(self, lines: List[LineWithMeta]) -> Tuple[List[LineWithMeta], List[LineWithMeta]]:
        document_name = []
        other_lines = []
        for line in lines:
            if line.hierarchy_level.level_1 == 0 and line.hierarchy_level.level_2 == 0:
                document_name.append(line)
            else:
                other_lines.append(line)
        return document_name, other_lines

    def __add_lists(self, not_document_name: List[LineWithMeta]):
        previous_hierarchy_level = None
        res = []
        for line in not_document_name:
            if line.hierarchy_level.is_list_item():
                if previous_hierarchy_level is None or previous_hierarchy_level < line.hierarchy_level:
                    list_line = self.__create_list_line(line)
                    res.append(list_line)
            if not line.hierarchy_level.is_raw_text():
                previous_hierarchy_level = line.hierarchy_level
            res.append(line)
        return res

    @staticmethod
    def __create_list_line(line: LineWithMeta):
        return LineWithMeta(line="",
                            hierarchy_level=HierarchyLevel(
                                level_1=line.hierarchy_level.level_1,
                                level_2=line.hierarchy_level.level_2 - 0.5,
                                paragraph_type="list",
                                can_be_multiline=False
                            ),
                            metadata=get_manager_config()['paragraph_metadata']().full_fields(paragraph_type="list",
                                                                                            page_id=line.metadata.page_id,
                                                                                            line_id=line.metadata.line_id,
                                                                                            predicted_classes=None),
                            annotations=[])
