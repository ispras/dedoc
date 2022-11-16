import re
from collections import defaultdict
from typing import List, Tuple, Optional, Iterator

import pandas as pd

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.utils_feature_extractor import normalization_by_min_max
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_item, regexps_digits_with_dots


class DiplomaFeatureExtractor(AbstractFeatureExtractor):

    named_item_regexp = re.compile(r"аннотация|введение|заключение|библиографический список|"
                                   r"приложени[ея]|глава")
    digits_with_dots_regexp = regexps_digits_with_dots
    only_digits_regexp = re.compile(r"^\s*\d+\s")

    def __init__(self) -> None:
        super().__init__()
        self.start_regexps = [
            regexps_item,  # list like 1.
            self.digits_with_dots_regexp,  # lists like 1.1.1. or 1.1.1
            self.only_digits_regexp,  # digits and space after them
            self.named_item_regexp  # keywords
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
        features_df["line_number_in_page"] = self._normalized_line_num_in_page(lines)

        page_ids = [line.metadata.page_id for line in lines]
        if page_ids:
            start_page, finish_page = min(page_ids), max(page_ids)
        else:
            start_page, finish_page = 0, 0

        one_line_features_dict = defaultdict(list)
        for line_id, line in enumerate(lines):
            for item in self._one_line_features(line, len(lines), start_page=start_page, finish_page=finish_page):
                feature_name, feature = item[0], item[1]
                one_line_features_dict[feature_name].append(feature)
        one_line_features_df = pd.DataFrame(one_line_features_dict)
        one_line_features_df["indentation"] = self._normalize_features(one_line_features_df.indentation)
        one_line_features_df = self.prev_next_line_features(one_line_features_df, 3, 3)

        result_matrix = pd.concat([one_line_features_df, features_df], axis=1)
        return result_matrix

    def _one_line_features(self,
                           line: LineWithMeta,
                           total_lines: int,
                           start_page: int,
                           finish_page: int) -> Iterator[Tuple[str, int]]:
        text = line.line.lower()
        # TODO dots list depth
        yield from self._start_regexp(line.line, self.start_regexps)
        yield ("named_item_regexp", 1) if self.named_item_regexp.match(text) else ("named_item_regexp", 0)
        yield ("is_upper", 1) if line.line.strip().isupper() else ("is_upper", 0)
        yield ("is_lower", 1) if line.line.strip().islower() else ("is_lower", 0)

        number = self.number_regexp.match(text)
        number = number.group().strip() if number else ""
        if number.endswith((')', '}')):
            number = number[:-1]
        yield ("dot_number_regexp", 1) if number.endswith(".") else ("dot_number_regexp", 0)
        yield "dot_number_regexp_len", len(number.split("."))
        yield "dot_number_regexp_max", max([int(n) for n in number.split(".") if n if n.isnumeric()], default=-1)

        yield "text_length", len(text)
        yield "words_number", len(text.split())
        yield "line_id", normalization_by_min_max(line.metadata.line_id, min_v=0, max_v=total_lines)

        yield "indentation", self._get_indentation(line)
        yield "font_size", self._get_size(line)
        yield "bold", self._get_bold(line)
        yield "page_id", normalization_by_min_max(line.metadata.page_id, min_v=start_page, max_v=finish_page)

    def _normalized_line_num_in_page(self, lines: List[LineWithMeta]) -> List[float]:
        page2lines = defaultdict(list)
        for line in lines:
            page2lines[line.metadata.page_id].append(line)
        page2lines = dict(page2lines)
        for key, value in page2lines.items():
            page2lines[key] = sorted(value, key=lambda x: x.metadata.line_id)
            page2lines[key] = dict(zip([line.uid for line in page2lines[key]],
                                       range(1, len(page2lines[key]) + 1)))

        result = []
        for line in lines:
            one_page_dict = page2lines[line.metadata.page_id]
            result.append(one_page_dict[line.uid] / len(one_page_dict))
        return result
