from typing import List, Optional, Tuple

from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_digits_with_dots
from dedoc.structure_extractors.patterns import BracketListPattern, BulletListPattern, DottedListPattern, LetterListPattern, TagListPattern, TagPattern


class DiplomaBodyBuilder(AbstractHierarchyLevelBuilder):
    named_item_keywords = ("введение", "заключение", "библиографический список", "список литературы", "глава", "приложение", "приложения")

    def __init__(self) -> None:
        super().__init__()
        self.digits_with_dots_regexp = regexps_digits_with_dots
        self.patterns = [
            TagListPattern(line_type=HierarchyLevel.list_item, level_1=2, can_be_multiline=False),
            DottedListPattern(line_type=HierarchyLevel.list_item, level_1=2, can_be_multiline=False),
            BracketListPattern(line_type=HierarchyLevel.list_item, level_1=3, level_2=1, can_be_multiline=False),
            LetterListPattern(line_type=HierarchyLevel.list_item, level_1=4, level_2=1, can_be_multiline=False),
            BulletListPattern(line_type=HierarchyLevel.list_item, level_1=5, level_2=1, can_be_multiline=False),
            TagPattern(line_type=HierarchyLevel.raw_text)
        ]

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        if len(lines_with_labels) > 0:
            line = lines_with_labels[0][0]
            page_id = line.metadata.page_id
            line_id = line.metadata.line_id
            body_line = AbstractBodyHierarchyLevelBuilder.get_body_line(page_id=page_id, line_id=line_id, init_hl_depth=init_hl_depth)
            result = [body_line]
        else:
            result = [AbstractBodyHierarchyLevelBuilder.get_body_line(init_hl_depth=init_hl_depth)]
        previous_named_item_line = None

        for line, prediction in lines_with_labels:
            if prediction == "named_item" or line.metadata.tag_hierarchy_level.line_type == "header":
                line = self.__handle_named_item(init_hl_depth, line, prediction, previous_named_item_line)
                previous_named_item_line = line
            elif prediction == "list_item":
                level = line.metadata.tag_hierarchy_level
                level_1 = previous_named_item_line.metadata.hierarchy_level.level_1 + level.level_1 - 1 if previous_named_item_line else \
                    init_hl_depth + level.level_1 - 1
                line.metadata.hierarchy_level = HierarchyLevel(level_1=level_1, level_2=level.level_2, line_type=prediction, can_be_multiline=True)
            elif prediction == "page_id":
                line.metadata.hierarchy_level = HierarchyLevel(level_1=None, level_2=None, line_type=prediction, can_be_multiline=False)
            elif prediction == "raw_text":
                line = self.__postprocess_raw_text(line, init_hl_depth)
                if not (line.metadata.hierarchy_level is not None and line.metadata.hierarchy_level.line_type == "named_item"):
                    line.metadata.hierarchy_level = self.__get_level_by_patterns(line)
            else:
                line.metadata.hierarchy_level = HierarchyLevel.create_raw_text()
                line.metadata.hierarchy_level.line_type = prediction
            result.append(line)
        return result

    def __handle_named_item(self, init_hl_depth: int, line: LineWithMeta, prediction: str, previous_named_item_line: Optional[LineWithMeta] = None)\
            -> LineWithMeta:
        text = line.line.strip().lower()
        item_depth = get_dotted_item_depth(text)

        if text.startswith(self.named_item_keywords):
            hierarchy_level = HierarchyLevel(init_hl_depth, 0, True, prediction)
        elif item_depth == -1:
            if previous_named_item_line:
                hierarchy_level = previous_named_item_line.metadata.hierarchy_level
            else:
                hierarchy_level = HierarchyLevel(init_hl_depth, 0, True, prediction)
        else:
            hierarchy_level = HierarchyLevel(init_hl_depth, item_depth - 1, True, prediction)
        line.metadata.hierarchy_level = hierarchy_level
        return line

    def __get_level_by_patterns(self, line: LineWithMeta) -> HierarchyLevel:
        line_pattern = None
        for pattern in self.patterns:
            if pattern.match(line):
                line_pattern = pattern
                break

        return line_pattern.get_hierarchy_level(line) if line_pattern else HierarchyLevel.create_raw_text()

    def __postprocess_raw_text(self, line: LineWithMeta, init_hl_depth: int) -> LineWithMeta:
        text = line.line.strip().lower()
        if not text.startswith(self.named_item_keywords):
            return line

        bold = [annotation for annotation in line.annotations if annotation.name == BoldAnnotation.name and annotation.value == "True"]
        if len(bold) == 0:
            return line

        return self.__handle_named_item(init_hl_depth, line, "named_item")
