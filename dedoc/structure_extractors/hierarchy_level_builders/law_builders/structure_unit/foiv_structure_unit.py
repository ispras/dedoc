from typing import Optional, Tuple

from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.structure_unit.abstract_structure_unit import AbstractStructureUnit
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_foiv_item, regexps_item_with_bracket, regexps_subitem


class FoivStructureUnitBuilder(AbstractStructureUnit):
    document_types = ["foiv"]
    regexps_item = regexps_foiv_item
    regexps_subitem_with_char = regexps_subitem
    regexps_subitem_with_number = regexps_item_with_bracket

    def structure_unit(self, text: str, init_hl_depth: int, previous_hl: Optional[HierarchyLevel]) -> Tuple[HierarchyLevel, Optional[HierarchyLevel]]:
        if text.lower().startswith("глава") or LawTextFeatures.roman_regexp.match(text):
            hl = HierarchyLevel(init_hl_depth + 4, 0, True, "chapter")
            return hl, hl

        match_subitem = self.regexps_subitem_with_number.match(text)
        if match_subitem:
            nodes = [i for i in text[match_subitem.start(): match_subitem.end()].split(".") if len(i.strip()) > 0]
            hl = HierarchyLevel(init_hl_depth + 9, len(nodes), False, "subitem")
            return hl, hl
        match_subitem = self.regexps_subitem_with_char.match(text)
        if match_subitem:
            nodes = [i for i in text[match_subitem.start(): match_subitem.end()].split(".") if len(i.strip()) > 0]
            hl = HierarchyLevel(init_hl_depth + 10, len(nodes), False, "subitem")
            return hl, hl
        match_item = self.regexps_item.match(text)
        if match_item:
            nodes = [i for i in text[match_item.start(): match_item.end()].split(".") if len(i.strip()) > 0]
            hl = HierarchyLevel(init_hl_depth + 8, len(nodes), False, "item")
            return hl, hl
        elif previous_hl is not None:
            return previous_hl, previous_hl

        return HierarchyLevel(None, None, False, HierarchyLevel.raw_text), None
