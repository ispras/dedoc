import re
from typing import List
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.line_with_meta import HierarchyLevel
from dedoc.data_structures.line_with_meta import ParagraphMetadata
from dedoc.structure_constructor.concreat_structure_constructors.list_item import ListItem


class ListPatcher:
    def __init__(self):
        self.list_line_regexp = re.compile(r' *\d+(?:\.\d+|)*[ .)].*')
        self.list_item_regexp = re.compile(r' *\d+(?:\.\d+|)*[ .)]')

    def __is_list(self, line: str) -> bool:
        return self.list_line_regexp.fullmatch(line) is not None

    def __get_list_item(self, line: str) -> ListItem:
        list_item = self.list_item_regexp.search(line).group(0).lstrip()
        items = [int(item) for item in list_item[:-1].split(r'.') if item]
        return ListItem(items, list_item[-1:])

    def __have_parent(self, items: List[ListItem], parent: ListItem) -> int:
        for item in items[::-1]:
            if parent == item:
                return True

        return False

    def __have_type(self, items: List[ListItem], end_type: str) -> bool:
        for item in items[::-1]:
            if item.end_type == end_type:
                return True

        return False

    def __get_inserting_parents(self, parent: ListItem, items: List[ListItem], levels: List[HierarchyLevel]) -> List[ListItem]:
        if self.__have_parent(items, parent):
            while items[-1] != parent:
                levels.pop()
                items.pop()

        if self.__have_type(items, parent.end_type):
            while parent.end_type != items[-1].end_type:
                items.pop()
                levels.pop()

        inserting = []

        while parent != items[-1] and items[-1] < parent:
            inserting.append(parent)
            parent = parent.get_parent()

        return inserting

    def __patch_list(self, line: LineWithMeta, items: List[ListItem], levels: List[HierarchyLevel], parent: ListItem):
        inserting = self.__get_inserting_parents(parent, items, levels)
        patched_lines = []

        while inserting:
            last = inserting.pop()
            item_str = str(last)
            paragraph_type = HierarchyLevel.raw_text if levels[-1].level_1 is None else HierarchyLevel.list_item
            hierarchy_level = HierarchyLevel(level_1=levels[-1].level_1,
                                             level_2=len(last.item),
                                             paragraph_type=paragraph_type,
                                             can_be_multiline=False)

            patched_lines.append(LineWithMeta(line=item_str,
                                              hierarchy_level=hierarchy_level,
                                              metadata=ParagraphMetadata(paragraph_type="list_item",
                                                                         page_id=line.metadata.page_id,
                                                                         line_id=line.metadata.line_id,
                                                                         predicted_classes=None),
                                              annotations=[]))

            items.append(last)
            levels.append(hierarchy_level)

        return patched_lines

    def __update_line_levels(self, lines: List[LineWithMeta], list_item_line: LineWithMeta):
        for line in lines:
            level_1 = list_item_line.hierarchy_level.level_1
            level_2 = list_item_line.hierarchy_level.level_2
            can_be_multiline = line.hierarchy_level.can_be_multiline
            paragraph_type = line.hierarchy_level.paragraph_type
            level = HierarchyLevel(level_1, 1 if level_2 is None else level_2 + 1, can_be_multiline, paragraph_type)
            line.set_hierarchy_level(level)

    def patch(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        items = []
        levels = []
        patched_lines = []
        content = []

        for line in lines:
            if not self.__is_list(line.line):
                content.append(line)
                continue

            item = self.__get_list_item(line.line)
            parent = item.get_parent()

            if not item.is_first_item() and items:
                self.__update_line_levels(content, line)

                if parent != items[-1]:
                    patched_lines.extend(self.__patch_list(line, items, levels, parent))

            patched_lines.extend(content)
            content = []

            items.append(item)
            levels.append(line.hierarchy_level)
            patched_lines.append(line)

        patched_lines.extend(content)
        return patched_lines
