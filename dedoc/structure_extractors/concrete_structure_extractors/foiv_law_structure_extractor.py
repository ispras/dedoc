from typing import List, Optional

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.concrete_structure_extractors.abstract_law_structure_extractor import AbstractLawStructureExtractor
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_foiv_hierarchy_level_builder import \
    ApplicationFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_foiv_hierarchy_level_builder import BodyFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.cellar_builder import CellarHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_ends_of_number, regexps_foiv_item


class FoivLawStructureExtractor(AbstractLawStructureExtractor):
    """
    This class is used for extraction structure from foiv type of law.

    You can find the description of this type of structure in the section :ref:`foiv_law_structure`.
    """
    document_type = "foiv_law"

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.hierarchy_level_builders = [
            HeaderHierarchyLevelBuilder(),
            BodyFoivHierarchyLevelBuilder(),
            CellarHierarchyLevelBuilder(),
            ApplicationFoivHierarchyLevelBuilder()
        ]
        self.regexps_subitem_with_number = BodyFoivHierarchyLevelBuilder.regexps_subitem_with_number
        self.regexps_subitem_with_char = BodyFoivHierarchyLevelBuilder.regexps_subitem_with_char
        self.regexps_ends_of_number = regexps_ends_of_number
        self.init_hl_depth = 2
        self.hl_type = "foiv"

    def _postprocess_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        return self._postprocess(lines=lines,
                                 paragraph_type=["item", "subitem", "subitem"],
                                 regexps=[regexps_foiv_item, self.regexps_subitem_with_number, self.regexps_subitem_with_char],
                                 excluding_regexps=[None, self.regexps_ends_of_number, None])
