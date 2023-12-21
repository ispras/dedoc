import re
from typing import List, Optional

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.concrete_structure_extractors.abstract_law_structure_extractor import AbstractLawStructureExtractor
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_law_hierarchy_level_builder import \
    ApplicationLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_law_hierarchy_level_builder import BodyLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.cellar_builder import CellarHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_ends_of_number, regexps_number


class LawStructureExtractor(AbstractLawStructureExtractor):
    """
    This class is used for extraction structure from common laws.

    You can find the description of this type of structure in the section :ref:`simple_law_structure`.
    """
    document_type = "law"

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.hierarchy_level_builders = [
            HeaderHierarchyLevelBuilder(),
            BodyLawHierarchyLevelBuilder(),
            CellarHierarchyLevelBuilder(),
            ApplicationLawHierarchyLevelBuilder()
        ]
        self.regexps_item = re.compile(r"^\s*(\d*\.)*\d+[\)|\}]")
        self.regexps_part = regexps_number
        self.regexps_subitem = re.compile(r"^\s*[а-яё]\)")
        self.regexps_ends_of_number = regexps_ends_of_number
        self.init_hl_depth = 2
        self.hl_type = "law"

    def _postprocess_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        return self._postprocess(lines=lines,
                                 paragraph_type=["item", "articlePart", "subitem"],
                                 regexps=[self.regexps_item, self.regexps_part, self.regexps_subitem],
                                 excluding_regexps=[None, self.regexps_ends_of_number, self.regexps_ends_of_number])
