from typing import List, Tuple

from dedoc.data_structures import BoldAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors import DefaultStructureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.abstract_body_hierarchy_level_builder import \
    AbstractBodyHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_digits_with_dots


class DiplomaBodyBuilder(AbstractHierarchyLevelBuilder):
    named_item_keywords = ("введение", "заключение", "библиографический список", "список литературы", "глава", "приложение", "приложения")

    def __int__(self) -> None:
        super().__init__()
        self.digits_with_dots_regexp = regexps_digits_with_dots

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        if len(lines_with_labels) > 0:
            line = lines_with_labels[0][0]
            page_id = line.metadata.page_id
            line_id = line.metadata.line_id
            body_line = AbstractBodyHierarchyLevelBuilder.get_body_line(page_id=page_id, line_id=line_id, init_hl_depth=init_hl_depth)
            result = [body_line]
        else:
            result = [AbstractBodyHierarchyLevelBuilder.get_body_line(init_hl_depth=init_hl_depth)]
        previous_raw_text_line = None
        previous_named_item_line = None

        for line, prediction in lines_with_labels:
            if prediction == "named_item" or line.metadata.tag_hierarchy_level.line_type == "header":
                line = self.__handle_named_item(init_hl_depth, line, prediction)
                previous_named_item_line = line

            elif prediction == "list_item":
                level = line.metadata.tag_hierarchy_level
                level_1 = previous_named_item_line.metadata.hierarchy_level.level_1 + level.level_1 - 1 if previous_named_item_line else \
                    init_hl_depth + level.level_1 - 1
                line.metadata.hierarchy_level = HierarchyLevel(level_1=level_1, level_2=level.level_2, line_type=prediction, can_be_multiline=False)

            elif prediction == "raw_text":
                line = self.__postprocess_raw_text(line, init_hl_depth)
                if not (line.metadata.hierarchy_level is not None and line.metadata.hierarchy_level.line_type == "named_item"):
                    line.metadata.hierarchy_level = DefaultStructureExtractor.get_list_hl_with_regexp(line, previous_raw_text_line)
                    previous_raw_text_line = line
            else:
                line.metadata.hierarchy_level = HierarchyLevel.create_raw_text()
                line.metadata.hierarchy_level.line_type = prediction
            result.append(line)
        return result

    def __handle_named_item(self, init_hl_depth: int, line: LineWithMeta, prediction: str) -> LineWithMeta:
        text = line.line.strip().lower()
        item_depth = get_dotted_item_depth(text)

        if text.startswith(self.named_item_keywords):
            hierarchy_level = HierarchyLevel(init_hl_depth, 0, True, prediction)
        elif item_depth == -1:
            hierarchy_level = HierarchyLevel(init_hl_depth + 1, 0, True, prediction)
        else:
            hierarchy_level = HierarchyLevel(init_hl_depth, item_depth - 1, True, prediction)
        line.metadata.hierarchy_level = hierarchy_level
        return line

    def __postprocess_raw_text(self, line: LineWithMeta, init_hl_depth: int) -> LineWithMeta:
        text = line.line.strip().lower()
        if not text.startswith(self.named_item_keywords):
            return line

        bold = [annotation for annotation in line.annotations if annotation.name == BoldAnnotation.name and annotation.value == "True"]
        if len(bold) == 0:
            return line

        return self.__handle_named_item(init_hl_depth, line, "named_item")
