import re
from collections import defaultdict
from typing import List, Tuple, Optional, Iterator

import pandas as pd

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_prefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.utils_feature_extractor import normalization_by_min_max
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_item, regexps_digits_with_dots


class DiplomaFeatureExtractor(AbstractFeatureExtractor):

    def __init__(self) -> None:
        super().__init__()
        self.named_item_keywords = ("аннотация", "abstract", "введение", "заключение", "библиографическийсписок", "списоклитературы")
        self.named_item_start = ("приложение", "глава")
        self.titles = ("бакалаврскаяработа", "магистерскаядиссертация", "выпускнаяквалификационнаяработа", "курсоваяработа")
        self.title_keywords = ("автор:", "руководитель:", "научныйруководитель:")
        self.year_regexp = re.compile(r"20\d\dг\.$")
        self.digits_with_dots_regexp = regexps_digits_with_dots
        self.only_digits_regexp = re.compile(r"^\s*\d+\s")

        self.start_regexps = [
            regexps_item,  # list like 1.
            self.digits_with_dots_regexp,  # lists like 1.1.1. or 1.1.1
            self.only_digits_regexp,  # digits and space after them
        ]
        self.list_feature_extractor = ListFeaturesExtractor()

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[LineWithMeta], y: Optional[List[str]] = None) -> "DiplomaFeatureExtractor":
        return self

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        result_matrix = pd.concat([self.__process_document(document) for document in documents], ignore_index=True)
        features = sorted(result_matrix.columns)
        return result_matrix[features].astype(float)

    def __process_document(self, lines: List[LineWithMeta]) -> pd.DataFrame:
        _, features_df = self.list_feature_extractor.one_document(lines)
        features_df["list_item"] = self._list_features(lines)

        one_line_features_dict = defaultdict(list)
        for line_id, line in enumerate(lines):
            for item in self._one_line_features(line, len(lines)):
                feature_name, feature = item[0], item[1]
                one_line_features_dict[feature_name].append(feature)
        one_line_features_df = pd.DataFrame(one_line_features_dict)
        one_line_features_df["indentation"] = self._normalize_features(one_line_features_df.indentation)
        one_line_features_df = self.prev_next_line_features(one_line_features_df, 3, 3)

        result_matrix = pd.concat([one_line_features_df, features_df], axis=1)
        return result_matrix

    def _one_line_features(self, line: LineWithMeta, total_lines: int) -> Iterator[Tuple[str, int]]:
        text = line.line.lower()
        text_wo_spaces = "".join(text.strip().split())
        yield "is_title", int(text_wo_spaces in self.titles)
        yield "is_title_keyword", int(text_wo_spaces in self.title_keywords)
        yield "is_named_item", int(text_wo_spaces in self.named_item_keywords)
        yield "named_item_start", int(text_wo_spaces.startswith(self.named_item_start))

        match = self.year_regexp.match(text)
        yield "contains_year", int(match is not None)
        yield from self._start_regexp(line.line, self.start_regexps)

        yield "is_upper", int(line.line.strip().isupper())
        yield "is_lower", int(line.line.strip().islower())

        prefix = get_prefix([DottedPrefix], line)
        yield ("dotted_depth", len(prefix.numbers)) if prefix.name == DottedPrefix.name else ("dotted_depth", 0)

        yield "text_length", len(text.strip())
        yield "words_number", len(text.strip().split())
        yield "line_id", normalization_by_min_max(line.metadata.line_id, min_v=0, max_v=total_lines)
        # TODO work with page number (if it will be added to docx correctly)

        yield "indentation", self._get_indentation(line)
        yield "font_size", self._get_size(line)
        yield "bold", self._get_bold(line)
        yield "bold_percent", self._get_bold_percent(line)
        yield "italic", self._get_italic(line)
        yield "underlined", self._get_underlined(line)
