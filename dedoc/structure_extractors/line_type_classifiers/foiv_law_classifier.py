from typing import List, Iterator

from xgboost import XGBClassifier

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.header_builder.header_hierarchy_level_builder import \
    HeaderHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.application_builder.application_foiv_hierarchy_level_builder import \
    ApplicationFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.body_builder.body_foiv_hierarchy_level_builder import \
    BodyFoivHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.law_builders.cellar_builder import \
    CellarHierarchyLevelBuilder
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_foiv_item
from dedoc.structure_extractors.line_type_classifiers.abstract_law_classifier import AbstractLawLineTypeClassifier


class FoivLawLineTypeClassifier(AbstractLawLineTypeClassifier):
    document_type = "foiv_law"

    def __init__(self, classifier: XGBClassifier, feature_extractor: LawTextFeatures, *, config: dict) -> None:
        super().__init__(classifier, feature_extractor, config=config)

        self.regexps_subitem_with_number = BodyFoivHierarchyLevelBuilder.regexps_subitem_with_number
        self.regexps_subitem_with_char = BodyFoivHierarchyLevelBuilder.regexps_subitem_with_char

        self.__init_hl_depth = 2
        self.hl_type = "foiv"
        self._chunk_hl_builders = [HeaderHierarchyLevelBuilder(),
                                   BodyFoivHierarchyLevelBuilder(),
                                   CellarHierarchyLevelBuilder(),
                                   ApplicationFoivHierarchyLevelBuilder()]

    @staticmethod
    def load_pickled(path: str = None, *, config: dict) -> "FoivLawLineTypeClassifier":
        classifier, feature_extractor_parameters = AbstractLawLineTypeClassifier._load_gzipped_xgb(path=path)
        return FoivLawLineTypeClassifier(classifier=classifier,
                                         feature_extractor=LawTextFeatures(**feature_extractor_parameters),
                                         config=config)

    def _law_line_postprocess(self, lines: List[LineWithMeta]) -> Iterator[LineWithMeta]:
        yield from self._line_postprocess(lines=lines,
                                          paragraph_type=["item", "subitem", "subitem"],
                                          regexps=[regexps_foiv_item,
                                                   self.regexps_subitem_with_number,
                                                   self.regexps_subitem_with_char],
                                          excluding_regexps=[None,
                                                             self.ends_of_number,
                                                             None])
