from typing import Tuple, List, Optional

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.list_features.prefix.non_letter_prefix import NonLetterPrefix
from dedoc.structure_extractors.feature_extractors.tz_feature_extractor import TzTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder


class TzBodyBuilder(AbstractHierarchyLevelBuilder):

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
            if prediction in ("part", "named_item", "item"):
                line = self.__handle_item(init_hl_depth, line, prediction, previous_hl=previous_hl)
                previous_hl = line.hierarchy_level
                result.append(line)
            else:
                line.set_hierarchy_level(HierarchyLevel.create_raw_text())
                line.metadata.paragraph_type = "raw_text"
                result.append(line)
        return result

    def __handle_item(self,
                      init_hl_depth: int,
                      line: LineWithMeta,
                      prediction: str,
                      previous_hl: Optional[HierarchyLevel]) -> LineWithMeta:
        text = line.line.lower().strip()
        item_min_depth = 5 + init_hl_depth
        if prediction == "part":
            hierarchy_level = HierarchyLevel(init_hl_depth + 1, 0, True, prediction)
        elif TzTextFeatures.named_item_regexp.match(text):
            if "подраздел" in text:
                hierarchy_level = HierarchyLevel(item_min_depth + 2, 1, False, prediction)
            else:
                hierarchy_level = HierarchyLevel(item_min_depth + 2, 0, False, prediction)
        elif TzTextFeatures.number_regexp.match(text):
            match = TzTextFeatures.number_regexp.match(text)
            number = text[match.start(): match.end()]
            number_splitted = [n for n in number.strip().split('.') if n.isnumeric()]
            hierarchy_level = HierarchyLevel(item_min_depth + 3, len(number_splitted), False, prediction)
        elif NonLetterPrefix.regexp.match(text):
            hierarchy_level = HierarchyLevel(item_min_depth + 4, 0, False, prediction)
        elif TzTextFeatures.item_regexp.match(text):
            hierarchy_level = HierarchyLevel(item_min_depth + 4, 0, False, prediction)
        else:
            hierarchy_level = HierarchyLevel.create_raw_text()
        if previous_hl is not None and previous_hl <= hierarchy_level and not hierarchy_level.is_raw_text():
            if previous_hl.level_1 == hierarchy_level.level_1 and previous_hl.level_2 == previous_hl.level_2:
                hierarchy_level.paragraph_type = previous_hl.paragraph_type
            elif previous_hl < hierarchy_level and previous_hl.paragraph_type == "item":
                hierarchy_level.paragraph_type = previous_hl.paragraph_type
        line.set_hierarchy_level(hierarchy_level)
        line.metadata.paragraph_type = hierarchy_level.paragraph_type
        return line