from typing import List, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder


class TocBuilder(AbstractHierarchyLevelBuilder):
    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        # TODO add analyse toc if tag 'toc' and 'toc_item' exist
        result = []
        is_toc_begun = False
        for line, _ in lines_with_labels:
            if line.line.lower().strip() in ("содержание", "оглавление"):  # set line as toc
                line.metadata.hierarchy_level = HierarchyLevel(init_hl_depth + 0, 0, False, "toc")
                result.append(line)
                is_toc_begun = True
                continue
            elif not is_toc_begun:
                result.append(self.__get_toc_line(line, init_hl_depth=init_hl_depth))
            is_toc_begun = True
            line.metadata.hierarchy_level = HierarchyLevel(init_hl_depth + 1, 0, False, "toc_item")
            result.append(line)
        return result

    def __get_toc_line(self, line: LineWithMeta, init_hl_depth: int) -> LineWithMeta:
        return LineWithMeta(line="",
                            metadata=LineMetadata(hierarchy_level=HierarchyLevel(init_hl_depth + 0, 0, False, "toc"),
                                                  page_id=line.metadata.page_id,
                                                  line_id=line.metadata.line_id),
                            annotations=[],
                            uid=line.uid + "_toc")
