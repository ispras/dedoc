from typing import List, Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bullet_prefix import BulletPrefix
from dedoc.structure_extractors.feature_extractors.tz_feature_extractor import TzTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_number, regexps_subitem


class TzBodyBuilder(AbstractHierarchyLevelBuilder):

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        if len(lines_with_labels) > 0:
            line = lines_with_labels[0][0]
            page_id = line.metadata.page_id
            line_id = line.metadata.line_id
            body_line = AbstractBodyHierarchyLevelBuilder.get_body_line(page_id=page_id, line_id=line_id, init_hl_depth=init_hl_depth)
            result = [body_line]
        else:
            result = [AbstractBodyHierarchyLevelBuilder.get_body_line(init_hl_depth=init_hl_depth)]
        previous_hl = None
        for line, prediction in lines_with_labels:
            if prediction in ("part", "named_item", "item"):
                # TODO: add analyse tag "header" if tag exist then analyse what type of header here by using regexps
                #  (part, named_item, number, NonLetterPrefix.regexp, TzTextFeatures.item_regexp )
                #  Q: set HL of tag "header"? A: (need analyse document) in some all headers can have the same HL, in the other document otherside
                #  I think we must set HL of regular expression
                #  For Understanding header you need example of doc files.
                line = self.__handle_item(init_hl_depth, line, prediction, previous_hl=previous_hl)
                previous_hl = line.metadata.hierarchy_level
                result.append(line)
            else:
                line.metadata.hierarchy_level = HierarchyLevel.create_raw_text()
                result.append(line)
        return result

    def __handle_item(self, init_hl_depth: int, line: LineWithMeta, prediction: str, previous_hl: Optional[HierarchyLevel]) -> LineWithMeta:
        text = line.line.lower().strip()
        item_min_depth = 5 + init_hl_depth
        if prediction == "part":
            hierarchy_level = HierarchyLevel(init_hl_depth + 1, 0, True, prediction)
        elif TzTextFeatures.named_item_regexp.match(text):
            if "подраздел" in text:
                hierarchy_level = HierarchyLevel(item_min_depth + 2, 1, False, prediction)
            else:
                hierarchy_level = HierarchyLevel(item_min_depth + 2, 0, False, prediction)
        elif regexps_number.match(text):
            match = regexps_number.match(text)
            number = text[match.start(): match.end()]
            number_splitted = [n for n in number.strip().split(".") if n.isnumeric()]
            hierarchy_level = HierarchyLevel(item_min_depth + 3, len(number_splitted), False, prediction)
        elif BulletPrefix.regexp.match(text):
            hierarchy_level = HierarchyLevel(item_min_depth + 4, 0, False, prediction)
        elif regexps_subitem.match(text):
            hierarchy_level = HierarchyLevel(item_min_depth + 4, 0, False, prediction)
        else:
            hierarchy_level = HierarchyLevel.create_raw_text()
        if previous_hl is not None and previous_hl <= hierarchy_level and not hierarchy_level.is_raw_text():
            if previous_hl.level_1 == hierarchy_level.level_1 and previous_hl.level_2 == previous_hl.level_2:
                hierarchy_level.line_type = previous_hl.line_type
            elif previous_hl < hierarchy_level and previous_hl.line_type == "item":
                hierarchy_level.line_type = previous_hl.line_type
        line.metadata.hierarchy_level = hierarchy_level
        return line
