from typing import Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class TagPattern(AbstractPattern):
    _name = "tag"

    def __init__(self,
                 line_type: Optional[str] = None,
                 level_1: Optional[int] = None,
                 level_2: Optional[int] = None,
                 can_be_multiline: Optional[bool or str] = None,
                 default_line_type: str = HierarchyLevel.raw_text,
                 default_level_1: Optional[int] = None,
                 default_level_2: Optional[int] = None) -> None:
        super().__init__(line_type=line_type, level_1=level_1, level_2=level_2, can_be_multiline=can_be_multiline)
        self._can_be_multiline_none = can_be_multiline is None
        self._default_line_type = default_line_type
        self._default_level_1 = default_level_1
        self._default_level_2 = default_level_2

    def match(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level is not None

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=self._get_line_type(line),
            level_1=self._get_level_1(line),
            level_2=self._get_level_2(line),
            can_be_multiline=self._get_can_be_multiline(line)
        )

    def _get_line_type(self, line: LineWithMeta) -> str:
        if self._line_type is not None:
            return self._line_type

        return self._default_line_type if line.metadata.tag_hierarchy_level.is_unknown() else line.metadata.tag_hierarchy_level.line_type

    def _get_level_1(self, line: LineWithMeta) -> Optional[int]:
        if self._level_1 is not None:
            return self._level_1

        return self._default_level_1 if line.metadata.tag_hierarchy_level.level_1 is None else line.metadata.tag_hierarchy_level.level_1

    def _get_level_2(self, line: LineWithMeta) -> Optional[int]:
        if self._level_2 is not None:
            return self._level_2

        return self._default_level_2 if line.metadata.tag_hierarchy_level.level_2 is None else line.metadata.tag_hierarchy_level.level_2

    def _get_regexp_level_2(self, line: LineWithMeta) -> int:
        if self._level_2 is not None:
            return self._level_2
        elif line.metadata.tag_hierarchy_level.level_2 is not None:
            return line.metadata.tag_hierarchy_level.level_2
        elif self._default_level_2 is not None:
            return self._default_level_2

        from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth
        depth = get_dotted_item_depth(line.line.strip())
        return depth if depth > 0 else 1

    def _get_can_be_multiline(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level.can_be_multiline if self._can_be_multiline_none else self._can_be_multiline
