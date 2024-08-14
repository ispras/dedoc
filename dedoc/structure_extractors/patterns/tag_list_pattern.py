from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class TagListPattern(AbstractPattern):
    _name = "tag_list"

    def match(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level is not None and line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.list_item

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        level_1, level_2 = self._get_level_1(line), self._get_level_2(line)
        return HierarchyLevel(
            line_type=self._get_line_type(line),
            level_1=level_1 if level_1 is not None else 2,
            level_2=level_2 if level_2 is not None else 1,
            can_be_multiline=self._get_can_be_multiline(line)
        )
