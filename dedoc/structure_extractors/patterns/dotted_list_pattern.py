from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern


class DottedListPattern(RegexpPattern):
    _name = "dotted_list"

    def __init__(self, line_type: str, level_1: int, can_be_multiline: Optional[bool or str] = None) -> None:
        super().__init__(regexp=DottedPrefix.regexp, line_type=line_type, level_1=level_1, level_2=None, can_be_multiline=can_be_multiline)

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=self._line_type,
            level_1=self._level_1,
            level_2=self.__get_list_depth(line=line),
            can_be_multiline=self._can_be_multiline
        )

    def __get_list_depth(self, line: LineWithMeta) -> int:
        text = line.line.strip().lower()
        match = self._regexp.match(text)
        if match is None:
            raise ValueError(f'Line text "{text}" does not match dotted list pattern regexp')

        prefix = match.group().strip()
        return len([number for number in prefix.split(".") if len(number) > 0])
