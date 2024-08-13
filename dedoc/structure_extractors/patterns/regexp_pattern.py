import re
from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class RegexpPattern(AbstractPattern):
    __name = "regexp"

    def __init__(self, regexp: str or re.Pattern, line_type: str, level_1: int, level_2: Optional[int] = None, can_be_multiline: bool = False) -> None:
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
        self._regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def match(self, line: LineWithMeta) -> bool:
        text = line.line.strip().lower()
        match = self._regexp.match(text)
        return match is not None

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(line_type=self._line_type, level_1=self._level_1, level_2=self._level_2, can_be_multiline=self._can_be_multiline)
