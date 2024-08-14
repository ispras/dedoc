from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class TagHeaderPattern(AbstractPattern):
    _name = "tag_header"

    def match(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level is not None and line.metadata.tag_hierarchy_level.line_type == HierarchyLevel.header
