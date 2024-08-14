from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class TagTypePattern(AbstractPattern):
    __name = "tag_type"

    def match(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level is not None and not line.metadata.tag_hierarchy_level.is_unknown()

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(
            line_type=line.metadata.tag_hierarchy_level.line_type,
            level_1=self._get_level_1(line),
            level_2=self._get_level_2(line),
            can_be_multiline=self._get_can_be_multiline(line)
        )
