from typing import List

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


class PatternComposition:
    """
    Class for applying patterns to get line's hierarchy level.

    Example of usage:

    .. code-block:: python

        from dedoc.data_structures.line_with_meta import LineWithMeta
        from dedoc.structure_extractors.patterns import TagListPattern, TagPattern
        from dedoc.structure_extractors.patterns.pattern_composition import PatternComposition


        pattern_composition = PatternComposition(
            patterns=[
                TagListPattern(line_type="list_item", default_level_1=2, can_be_multiline=False),
                TagPattern(default_line_type="raw_text")
            ]
        )
        line = LineWithMeta(line="Some text")
        line.metadata.hierarchy_level = pattern_composition.get_hierarchy_level(line=line)
    """
    def __init__(self, patterns: List[AbstractPattern]) -> None:
        """
        Set the list of patterns to apply to lines.

        **Note:** the order of the patterns is important. More specific patterns should go first.
        Otherwise, they may be ignored because of the patterns which also are applicable to the given line.

        :param patterns: list of patterns to apply to lines.
        """
        self.patterns = patterns

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        """
        Choose the suitable pattern from the list of patterns for applying to the given line.
        The first applicable pattern will be chosen.
        If no applicable pattern was found, the default ``raw_text`` :class:`~dedoc.data_structures.HierarchyLevel` is used as result.

        :param line: line to get hierarchy level for.
        """
        line_pattern = None

        for pattern in self.patterns:
            if pattern.match(line):
                line_pattern = pattern
                break

        return line_pattern.get_hierarchy_level(line) if line_pattern else HierarchyLevel.create_raw_text()
