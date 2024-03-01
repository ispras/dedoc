from typing import Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.abstract_structure_unit import AbstractStructureUnit
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_ends_of_number, regexps_foiv_item, regexps_item_with_bracket, regexps_subitem


class LawStructureUnitBuilder(AbstractStructureUnit):
    document_types = ["law"]
    regexps_item_with_bracket = regexps_item_with_bracket
    regexps_part = regexps_foiv_item
    ends_of_number = regexps_ends_of_number
    regexps_subitem = regexps_subitem

    def structure_unit(self, text: str, init_hl_depth: int, previous_hl: Optional[HierarchyLevel]) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        if text.lower().startswith("часть"):
            hl = HierarchyLevel(init_hl_depth + 1, 0, True, "part")  # 3
            return hl, hl
        if text.lower().startswith("раздел"):
            hl = HierarchyLevel(init_hl_depth + 2, 0, True, "section")  # 4
            return hl, hl
        if LawTextFeatures.roman_regexp.match(text):  # match roman numbers
            hl = HierarchyLevel(init_hl_depth + 3, 0, True, "subsection")  # 5
            return hl, hl
        if text.lower().startswith("глава"):
            hl = HierarchyLevel(init_hl_depth + 4, 0, True, "chapter")  # 6
            return hl, hl
        if text.lower().startswith("§"):
            hl = HierarchyLevel(init_hl_depth + 5, 0, True, "paragraph")  # 7
            return hl, hl
        if text.lower().startswith("статья"):
            hl = HierarchyLevel(init_hl_depth + 6, 0, True, "article")  # 8
            return hl, hl
        # We should check item before the part case sometimes part does not contain dot
        match_item = self.regexps_item_with_bracket.match(text)
        if match_item:
            return HierarchyLevel(init_hl_depth + 8, 0, False, "item"), None  # 10
        match_part = self.regexps_part.match(text)
        if match_part:
            len(match_part.group().split("."))
            return HierarchyLevel(init_hl_depth + 7, 0, False, "articlePart"), None  # 9
        if self.regexps_subitem.match(text):
            return HierarchyLevel(init_hl_depth + 9, 0, False, "subitem"), None  # 11
        elif previous_hl is not None:
            return previous_hl, previous_hl
        return HierarchyLevel(None, None, False, HierarchyLevel.raw_text), None
