from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.concrete_structure_extractors.abstract_law_structure_extractor import \
    AbstractLawStructureExtractor
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import \
    HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_law_hierarchy_level_builder import \
    ApplicationLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_foiv_hierarchy_level_builder import \
    BodyFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_law_hierarchy_level_builder import \
    BodyLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.cellar_builder import CellarHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_ends_of_number, \
    regexps_foiv_item


class FoivLawStructureExtractor(AbstractLawStructureExtractor):
    document_type = "foiv_law"

    def __init__(self, path: str, txt_path: str, *, config: dict):
        super().__init__(path=path, txt_path=txt_path, config=config)
        self.hierarchy_level_builders = [HeaderHierarchyLevelBuilder(),
                                         BodyLawHierarchyLevelBuilder(),
                                         CellarHierarchyLevelBuilder(),
                                         ApplicationLawHierarchyLevelBuilder()]
        self.regexps_subitem_with_number = BodyFoivHierarchyLevelBuilder.regexps_subitem_with_number
        self.regexps_subitem_with_char = BodyFoivHierarchyLevelBuilder.regexps_subitem_with_char
        self.regexps_ends_of_number = regexps_ends_of_number
        self.init_hl_depth = 2
        self.hl_type = "foiv"

    def _postprocess_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        return self._postprocess(lines=lines,
                                 paragraph_type=["item", "subitem", "subitem"],
                                 regexps=[regexps_foiv_item,
                                          self.regexps_subitem_with_number,
                                          self.regexps_subitem_with_char],
                                 excluding_regexps=[None,
                                                    self.regexps_ends_of_number,
                                                    None])
