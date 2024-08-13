from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class TagHeaderPattern(AbstractPattern):
    __name = "tag_header"

    def match(self, line: LineWithMeta) -> bool:
        if line.metadata.tag_hierarchy_level is None or line.metadata.tag_hierarchy_level.line_type != HierarchyLevel.header:
            return False

        level_1, level_2 = line.metadata.tag_hierarchy_level.level_1, line.metadata.tag_hierarchy_level.level_2
        return level_1 is not None and level_2 is not None

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        level_2 = line.metadata.tag_hierarchy_level.level_2
        return HierarchyLevel(line_type=self._line_type, level_1=self._level_1, level_2=level_2, can_be_multiline=self._can_be_multiline)
