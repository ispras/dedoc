from typing import Tuple, List, Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_digits_with_dots


class DiplomaBodyBuilder(AbstractHierarchyLevelBuilder):

    def __int__(self) -> None:
        super().__init__()
        self.digits_with_dots_regexp = regexps_digits_with_dots

    def get_lines_with_hierarchy(self,
                                 lines_with_labels: List[Tuple[LineWithMeta, str]],
                                 init_hl_depth: int) -> List[LineWithMeta]:
        if len(lines_with_labels) > 0:
            line = lines_with_labels[0][0]
            page_id = line.metadata.page_id
            line_id = line.metadata.line_id
            body_line = AbstractBodyHierarchyLevelBuilder.get_body_line(page_id=page_id,
                                                                        line_id=line_id,
                                                                        init_hl_depth=init_hl_depth)
            result = [body_line]
        else:
            result = [AbstractBodyHierarchyLevelBuilder.get_body_line(init_hl_depth=init_hl_depth)]
        previous_hl = None
        for line, prediction in lines_with_labels:
            if prediction == "named_item":
                line = self.__handle_named_item(init_hl_depth, line, prediction, previous_hl=previous_hl)
                previous_hl = line.hierarchy_level
                result.append(line)
            else:
                line.set_hierarchy_level(HierarchyLevel.create_raw_text())
                line.metadata.paragraph_type = prediction
                result.append(line)
        return result

    def __handle_named_item(self,
                            init_hl_depth: int,
                            line: LineWithMeta,
                            prediction: str,
                            previous_hl: Optional[HierarchyLevel]) -> LineWithMeta:
        item_depth = self.__get_named_item_depth(line.line.lower().strip())
        if item_depth == -1:
            hierarchy_level = HierarchyLevel(init_hl_depth, 0, True, prediction) if previous_hl is None else previous_hl
        else:
            hierarchy_level = HierarchyLevel(init_hl_depth + item_depth, 0, True, prediction)
        line.set_hierarchy_level(hierarchy_level)
        line.metadata.paragraph_type = hierarchy_level.paragraph_type
        return line

    def __get_named_item_depth(self, text: str) -> int:
        match = DottedPrefix.regexp.match(text)
        if match:
            prefix = DottedPrefix(match.group().strip(), indent=0)
            return len(prefix.numbers)
        else:
            return -1
