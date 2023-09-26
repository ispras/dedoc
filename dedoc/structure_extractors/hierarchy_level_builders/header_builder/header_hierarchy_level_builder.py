from copy import deepcopy
from typing import List, Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder


class HeaderHierarchyLevelBuilder(AbstractHierarchyLevelBuilder):
    document_types = ["foiv", "law"]
    starting_line_types = ["header"]

    def _line_2level(self, text: str, label: str, init_hl_depth: int, previous_hl: HierarchyLevel = None) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        hl = HierarchyLevel.create_root()
        return hl, hl

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int = 2) -> List[LineWithMeta]:
        result = []
        # detect begin of body
        previous_hl = HierarchyLevel.create_root()

        for line, label in lines_with_labels:
            # postprocessing of others units
            hierarchy_level, previous_hl = self._line_2level(text=line.line, label=label, init_hl_depth=init_hl_depth, previous_hl=previous_hl)

            self._postprocess_roman(hierarchy_level, line)

            metadata = deepcopy(line.metadata)
            metadata.hierarchy_level = hierarchy_level
            line = LineWithMeta(line=line.line, metadata=metadata, annotations=line.annotations, uid=line.uid)
            result.append(line)
        return result
