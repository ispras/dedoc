from copy import deepcopy
from typing import List, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder


class CellarHierarchyLevelBuilder(AbstractHierarchyLevelBuilder):
    document_types = ["foiv", "law"]
    starting_line_types = ["cellar"]

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int = 2) -> List[LineWithMeta]:
        result = []
        # detect begin of body
        hierarchy_level = HierarchyLevel(level_1=init_hl_depth, level_2=0, can_be_multiline=True, line_type="cellar")

        for line, _ in lines_with_labels:
            # postprocessing of others units
            metadata = deepcopy(line.metadata)
            metadata.hierarchy_level = hierarchy_level
            line = LineWithMeta(line=line.line, metadata=metadata, annotations=line.annotations, uid=line.uid)
            result.append(line)
        return result
