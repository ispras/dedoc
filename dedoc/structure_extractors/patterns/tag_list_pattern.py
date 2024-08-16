from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.tag_pattern import TagPattern


class TagListPattern(TagPattern):
    _name = "tag_list"

    def __init__(self,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[bool or str] = None,
                 default_line_type: str = HierarchyLevel.list_item,
                 default_level_1: int = 2,
                 default_level_2: Optional[int] = None) -> None:
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline, default_line_type=default_line_type,
                         default_level_1=default_level_1, default_level_2=default_level_2)

    def match(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level is not None and line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.list_item

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=self._get_line_type(line),
            level_1=self._get_level_1(line),
            level_2=self._get_regexp_level_2(line),
            can_be_multiline=self._get_can_be_multiline(line)
        )
