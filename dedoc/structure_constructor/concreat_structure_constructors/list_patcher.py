import re
from typing import List
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.line_with_meta import HierarchyLevel
from dedoc.data_structures.line_with_meta import ParagraphMetadata


class ListPatcher:
    def __init__(self):
        self.list_line_regexp = re.compile(r' *\d+(?:\.\d+|)*.*')
        self.list_item_regexp = re.compile(r' *\d+(?:\.\d+|)*')

    def __is_list(self, line: str) -> bool:
        return self.list_line_regexp.fullmatch(line) is not None

    def __get_list_item(self, line: str) -> List[int]:
        item = self.list_item_regexp.search(line).group(0).lstrip()
        items = [int(list_item) for list_item in item.split(r'.') if list_item]
        return items

    def __get_parent(self, list_item: List[int]) -> List[int]:
        parent = [item for item in list_item]
        parent[-1] -= 1

        if parent[-1] == 0:
            parent.pop()

        return parent

    def __is_less(self, item1: List[int], item2: List[int]) -> bool:
        max_len = max(len(item1), len(item2))

        for i in range(max_len):
            d1 = item1[i] if i < len(item1) else 0
            d2 = item2[i] if i < len(item2) else 0

            if d1 != d2:
                return d1 < d2

        return False

    def __have_parent(self, items: List[List[int]], parent: List[int]) -> int:
        for item in items[::-1]:
            if self.__is_less(parent, item):
                return False

            if item == parent:
                return True

        return False

    def __patch_list(self, line: LineWithMeta, items: List[List[int]], levels: List[HierarchyLevel], parent: List[int]):
        if self.__have_parent(items, parent):
            while self.__is_less(items[-1], parent):
                levels.pop()
                items.pop()

        inserting = []

        while parent != items[-1] and self.__is_less(items[-1], parent):
            inserting.append(parent)
            parent = self.__get_parent(parent)

        patched_lines = []

        while inserting:
            last = inserting.pop()
            item_str = "".join(['{}.'.format(item) for item in last])
            hierarcy_level = HierarchyLevel(level_1=levels[-1].level_1,
                                            level_2=len(last),
                                            paragraph_type=HierarchyLevel.list_item,
                                            can_be_multiline=False)

            patched_lines.append(LineWithMeta(line=item_str,
                                              hierarchy_level=hierarcy_level,
                                              metadata=ParagraphMetadata(paragraph_type="list",
                                                                         page_id=line.metadata.page_id,
                                                                         line_id=line.metadata.line_id,
                                                                         predicted_classes=None),
                                              annotations=[]))

        return patched_lines

    def patch(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        items = []
        levels = []
        patched_lines = []

        for line in lines:
            if not self.__is_list(line.line):
                patched_lines.append(line)
                continue

            item = self.__get_list_item(line.line)
            parent = self.__get_parent(item)

            if items and parent != items[-1]:
                patched_lines.extend(self.__patch_list(line, items, levels, parent))

            items.append(item)
            levels.append(line.hierarchy_level)
            patched_lines.append(line)

        return patched_lines
