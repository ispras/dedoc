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
