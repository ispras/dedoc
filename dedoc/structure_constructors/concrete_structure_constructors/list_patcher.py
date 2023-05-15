import re
from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_constructors.concrete_structure_constructors.list_item import ListItem
from dedoc.data_structures.hierarchy_level import HierarchyLevel


class ListPatcher:
    def __init__(self) -> None:
        self.list_line_regexp = re.compile(r' *\d+(?:\.\d+|)*[ .)].*')
        self.list_item_regexp = re.compile(r' *\d+(?:\.\d+|)*[ .)]')

    def __is_list(self, line: str) -> bool:
        return self.list_line_regexp.fullmatch(line) is not None

    def __get_list_item(self, line: str) -> ListItem:
        list_item = self.list_item_regexp.search(line).group(0).lstrip()
        items = [int(item) for item in list_item[:-1].split(r'.') if item]
        return ListItem(items, list_item[-1:])

    def __update_line_levels(self, lines: List[LineWithMeta], list_item_line: LineWithMeta) -> None:
        for line in lines:
            level_1 = list_item_line.metadata.hierarchy_level.level_1
            level_2 = list_item_line.metadata.hierarchy_level.level_2
            can_be_multiline = line.metadata.hierarchy_level.can_be_multiline
            paragraph_type = line.metadata.hierarchy_level.line_type
            if level_1 is not None:
                level = HierarchyLevel(level_1, 1 if level_2 is None else level_2 + 1, can_be_multiline, paragraph_type)
            else:
                level = HierarchyLevel.create_raw_text()
            line.metadata.hierarchy_level = level

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

            if not item.is_first_item() and items:
                self.__update_line_levels(content, line)

            patched_lines.extend(content)
            content = []

            items.append(item)
            levels.append(line.metadata.hierarchy_level)
            patched_lines.append(line)

        patched_lines.extend(content)
        return patched_lines
