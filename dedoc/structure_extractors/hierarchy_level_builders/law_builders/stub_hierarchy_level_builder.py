from typing import List, Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder


class StubHierarchyLevelBuilder(AbstractHierarchyLevelBuilder):
    starting_line_types = ["no_tag"]

    def _line_2level(self, text: str, label: str, init_hl_depth: int, previous_hl: HierarchyLevel = None) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        pass

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        lines = [line for line, _ in lines_with_labels]
        return lines
