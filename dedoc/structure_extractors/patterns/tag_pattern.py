from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class TagPattern(AbstractPattern):
    _name = "tag"

    def match(self, line: LineWithMeta) -> bool:
        return line.metadata.tag_hierarchy_level is not None
