import abc
from copy import deepcopy
from typing import List, Optional, Tuple
from uuid import uuid1

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.abstract_hierarchy_level_builder import AbstractHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.abstract_structure_unit import AbstractStructureUnit
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_ends_of_number, regexps_item_with_bracket, regexps_number, regexps_subitem


class AbstractBodyHierarchyLevelBuilder(AbstractHierarchyLevelBuilder, abc.ABC):
    starting_line_types = ["body"]
    regexps_item = regexps_item_with_bracket
    regexps_part = regexps_number
    ends_of_number = regexps_ends_of_number
    regexps_subitem = regexps_subitem

    @property
    @abc.abstractmethod
    def structure_unit_builder(self) -> AbstractStructureUnit:
        pass

    @staticmethod
    def get_body_line(page_id: int = 0, line_id: int = 0, init_hl_depth: int = 1) -> LineWithMeta:
        # if line_with_label is None:
        line_uid = str(uuid1()) + "_body"
        page_id = page_id
        line_id = line_id
        return LineWithMeta(line="",
                            metadata=LineMetadata(hierarchy_level=HierarchyLevel(init_hl_depth, 0, False, "body"), page_id=page_id, line_id=line_id),
                            annotations=[],
                            uid=line_uid)

    def get_lines_with_hierarchy(self, lines_with_labels: List[Tuple[LineWithMeta, str]], init_hl_depth: int = 2) -> List[LineWithMeta]:
        result = []
        # detect begin of body
        is_body_begun = False
        previous_hl = HierarchyLevel.create_root()

        for line, label in lines_with_labels:

            # postprocessing of others units
            hierarchy_level, previous_hl = self._line_2level(text=line.line, label=label, init_hl_depth=init_hl_depth, previous_hl=previous_hl)
            self._postprocess_roman(hierarchy_level, line)

            hierarchy_level = deepcopy(hierarchy_level)
            if len(line.line.strip()) == 0:
                hierarchy_level.can_be_multiline = True
            metadata = deepcopy(line.metadata)
            metadata.hierarchy_level = hierarchy_level

            if hierarchy_level.line_type != HierarchyLevel.root and not is_body_begun:
                result.append(self.get_body_line(init_hl_depth=init_hl_depth))
                is_body_begun = True

            line = LineWithMeta(line=line.line, metadata=metadata, annotations=line.annotations, uid=line.uid)
            result.append(line)
        if not is_body_begun:
            result.append(self.get_body_line(init_hl_depth=init_hl_depth))
        return result

    def _line_2level(self, text: str, label: str, init_hl_depth: int, previous_hl: HierarchyLevel = None) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        text = text.strip()
        if label == "header":
            label = "raw_text"

        if (label in ("application", "raw_text", "cellar")) and LawTextFeatures.roman_regexp.match(text):
            label = "structure_unit"

        if label == "structure_unit":
            return self.structure_unit_builder.structure_unit(text=text, init_hl_depth=init_hl_depth, previous_hl=previous_hl)
        if label == "footer":
            return HierarchyLevel(None, None, False, HierarchyLevel.raw_text), None
        if label == "raw_text":
            if previous_hl is not None:
                if previous_hl.line_type in ["application", "chapter"]:
                    return previous_hl, previous_hl
            return HierarchyLevel(None, None, False, HierarchyLevel.raw_text), None

        if label == "Other":
            return HierarchyLevel(1, 1, False, "Other"), None

        if label == "application":
            return HierarchyLevel(None, None, False, HierarchyLevel.raw_text), None
        else:
            raise Exception(f"{text} {label}")
