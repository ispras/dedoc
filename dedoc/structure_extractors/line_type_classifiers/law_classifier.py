import re
from collections import namedtuple
from typing import List, Iterator

from xgboost import XGBClassifier

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import \
    HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_law_hierarchy_level_builder import \
    ApplicationLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_law_hierarchy_level_builder import \
    BodyLawHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.cellar_builder import \
    CellarHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_number
from dedoc.structure_extractors.line_type_classifiers.abstract_law_classifier import AbstractLawLineTypeClassifier

LineLevel = namedtuple("LineLevel", ["name", "level1", "level2", "multiline"])
TagWithLineId = namedtuple("TagWithLineId", ["tag", "line_id"])


class LawLineTypeClassifier(AbstractLawLineTypeClassifier):

    document_type = "law"

    def __init__(self, classifier: XGBClassifier,
                 feature_extractor: LawTextFeatures,
                 *, config: dict) -> None:
        super().__init__(classifier, feature_extractor, config=config)

        self.regexps_item = re.compile(r'^\s*(\d*\.)*\d+[\)|\}]')
        self.regexps_part = regexps_number
        self.regexps_subitem = re.compile(r'^\s*[а-яё]\)')

        self.__init_hl_depth = 2
        self.hl_type = "law"
        self._chunk_hl_builders = [HeaderHierarchyLevelBuilder(),
                                   BodyLawHierarchyLevelBuilder(),
                                   CellarHierarchyLevelBuilder(),
                                   ApplicationLawHierarchyLevelBuilder()]

    @staticmethod
    def load_pickled(path: str = None, *, config: dict) -> "LawLineTypeClassifier":
        classifier, feature_extractor_parameters = LawLineTypeClassifier._load_gzipped_xgb(path)

        return LawLineTypeClassifier(classifier=classifier,
                                     feature_extractor=LawTextFeatures(**feature_extractor_parameters),
                                     config=config)

    def _law_line_postprocess(self, lines: List[LineWithMeta]) -> Iterator[LineWithMeta]:
        yield from self._line_postprocess(lines=lines,
                                          paragraph_type=["item", "articlePart", "subitem"],
                                          regexps=[self.regexps_item,
                                                   self.regexps_part,
                                                   self.regexps_subitem],
                                          excluding_regexps=[None,
                                                             self.ends_of_number,
                                                             self.ends_of_number])
