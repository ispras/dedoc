import abc
import copy
from copy import deepcopy
from typing import List, Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.abstract_structure_unit import AbstractStructureUnit
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_item_with_bracket, regexps_number


class AbstractApplicationHierarchyLevelBuilder(AbstractHierarchyLevelBuilder, abc.ABC):
    starting_line_types = ["application"]
    regexps_item = regexps_item_with_bracket
    regexps_part = regexps_number
    regexp_application_begin = LawTextFeatures.regexp_application_begin

    @property
    @abc.abstractmethod
    def structure_unit_builder(self) -> AbstractStructureUnit:
        pass

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int) -> List[LineWithMeta]:
        if len(lines_with_labels) == 0:
            return []
        result = []
        # detect begin of body
        previous_hl = HierarchyLevel(level_1=init_hl_depth, level_2=0, can_be_multiline=True, line_type="application")

        lines_with_labels[0] = lines_with_labels[0][0], "application"
        previous_line_start_of_application = False
        for line_id, (line, label) in enumerate(lines_with_labels):
            # postprocessing of others units
            hierarchy_level, previous_hl = self._line_2level(text=line.line, label=label, init_hl_depth=init_hl_depth, previous_hl=previous_hl)
            assert previous_hl is None or hierarchy_level == previous_hl

            # postprocess multiple applications
            if self.regexp_application_begin.match(line.line.strip().lower()):
                hierarchy_level.can_be_multiline = previous_line_start_of_application
                previous_line_start_of_application = True
            elif line.line.strip() != "":
                previous_line_start_of_application = False

            self._postprocess_roman(hierarchy_level, line)

            metadata = deepcopy(line.metadata)
            hierarchy_level = copy.deepcopy(hierarchy_level)
            if line_id == 0:
                hierarchy_level.can_be_multiline = False
            metadata.hierarchy_level = hierarchy_level
            line = LineWithMeta(line=line.line, metadata=metadata, annotations=line.annotations, uid=line.uid)
            result.append(line)

        return result

    def _line_2level(self, text: str, label: str, init_hl_depth: int, previous_hl: HierarchyLevel = None) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        text = text.strip()
        if len(text) == 0:
            label = HierarchyLevel.raw_text
        if label in ("header", "cellar"):
            label = "application"
        if label == "raw_text" and LawTextFeatures.regexp_application_begin.match(text):
            label = "application"
        if (label == "application" or label == "raw_text") and LawTextFeatures.roman_regexp.match(text):
            label = "structure_unit"

        if label == "structure_unit":
            return self.structure_unit_builder.structure_unit(text=text, init_hl_depth=init_hl_depth, previous_hl=previous_hl)
        elif label == "footer":
            return HierarchyLevel(None, None, False, HierarchyLevel.raw_text), None
        elif label == "raw_text" and previous_hl is not None and previous_hl.line_type == "chapter":
            return previous_hl, previous_hl

        elif label == "raw_text" and previous_hl is None:
            return HierarchyLevel.create_raw_text(), None

        elif label == "Other":
            return HierarchyLevel(1, 1, False, "Other"), None

        elif label in ("application", "header", "raw_text"):
            application_continue = label == "raw_text" and previous_hl is not None and previous_hl.line_type == "application"
            if label == "application" or application_continue:
                hl = HierarchyLevel(init_hl_depth, 0, True, "application")
                return hl, hl
            else:
                return HierarchyLevel.create_raw_text(), None
        else:
            raise Exception(f"{text} {label}")
