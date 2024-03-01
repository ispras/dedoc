import re
from collections import defaultdict
from typing import Iterator, List, Optional, Tuple

import pandas as pd

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_prefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.roman_prefix import RomanPrefix
from dedoc.structure_extractors.feature_extractors.utils_feature_extractor import normalization_by_min_max
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_digits_with_dots, regexps_item


class ArticleFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self) -> None:
        self.named_item_keywords = ("abstract", "introduction", "relatedwork", "conclusion", "references", "appendix", "acknowledgements")
        self.caption_keywords = ("figure", "table", "listing", "algorithm")

        self.start_regexps = [
            regexps_item,  # list like 1.
            regexps_digits_with_dots,  # lists like 1.1.1. or 1.1.1
            re.compile(r"^\s*\d+\s"),  # digits and space after them
        ]
        self.list_feature_extractor = ListFeaturesExtractor(window_size=10, prefix_list=[DottedPrefix, RomanPrefix])

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[LineWithMeta], y: Optional[List[str]] = None) -> "ArticleFeatureExtractor":
        return self

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        # merge matrices for all documents into one
        result_matrix = pd.concat([self.__process_document(document) for document in documents], ignore_index=True)

        # sort columns names for reproducibility on different systems
        features = sorted(result_matrix.columns)
        return result_matrix[features].astype(float)

    def __process_document(self, lines: List[LineWithMeta]) -> pd.DataFrame:
        # features for numbered items
        _, list_features_df = self.list_feature_extractor.one_document(lines)
        list_features_df["list_item"] = self._list_features(lines)

        # other features
        features_dict = defaultdict(list)
        for line in lines:
            for feature_name, feature in self._one_line_features(line, len(lines)):
                features_dict[feature_name].append(feature)
        features_df = pd.DataFrame(features_dict)

        # features normalization
        features_df["indentation"] = self._normalize_features(features_df.indentation)
        features_df["font_size"] = self._normalize_features(features_df.font_size)

        # add features of 3 previous and 3 next neighbor lines
        features_df = self.prev_next_line_features(features_df, 3, 3)

        # merge all features in one matrix
        result_matrix = pd.concat([features_df, list_features_df], axis=1)
        return result_matrix

    def _one_line_features(self, line: LineWithMeta, total_lines: int) -> Iterator[Tuple[str, int]]:
        # visual features
        yield "indentation", self._get_indentation(line)
        yield "spacing", self._get_spacing(line)
        yield "font_size", self._get_size(line)
        yield "bold", self._get_bold(line)
        bold_percent = self._get_bold_percent(line)
        yield "bold_percent", bold_percent
        yield "fully_bold", int(bold_percent == 1.)

        # textual features
        text = line.line.lower()
        text_wo_spaces = "".join(text.strip().split())
        yield "is_named_item", int(text_wo_spaces in self.named_item_keywords)
        yield "is_caption", len([word for word in self.caption_keywords if word in text_wo_spaces])
        yield "digits_number", sum(c.isdigit() for c in text_wo_spaces)
        yield "at_number", text_wo_spaces.count("@")
        yield "is_lower", int(line.line.strip().islower())
        yield "is_upper", int(line.line.strip().isupper())
        yield from self._start_regexp(line.line, self.start_regexps)
        prefix = get_prefix([DottedPrefix], line)
        yield ("dotted_depth", len(prefix.numbers)) if prefix.name == DottedPrefix.name else ("dotted_depth", 0)

        # statistical features
        yield "text_length", len(text.strip())
        yield "words_number", len(text.strip().split())
        yield "line_id", normalization_by_min_max(line.metadata.line_id, min_v=0, max_v=total_lines)
