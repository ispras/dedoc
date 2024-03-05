import re
from collections import defaultdict
from typing import Dict, Iterator, List, Optional, Tuple

import pandas as pd

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.utils_feature_extractor import normalization_by_min_max
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_year


class LawTextFeatures(AbstractFeatureExtractor):

    list_feature_extractor = ListFeaturesExtractor()

    named_regexp = [
        re.compile(r"^(Статья|(Г|г)лава|ГЛАВА|ЧАСТЬ|Часть|Раздел|РАЗДЕЛ|\$|§)\s*((\d+\.*)+|[IVXХxхviУП]{1,3}\.?)\s*")
    ]
    roman_regexp = re.compile(r"\s*(I|Г|T|Т|II|П|III|Ш|ТУ|TУ|IV|V|У|VI|УТ|УT|VII|УТТ|VIII|I[XХ]|[XХ]|[XХ]I|[XХ]II)\.\s+")
    regexp_application_begin = re.compile(
        r"^(\'|\")?(((П|п)риложение)|((У|у)твержден)[оаы]?){1}(( )*([№nN]?( )*(\d){1,3})?( )*)"
        r"((к распоряжению)|(к постановлению)|(к приказу))?\s*$"
    )
    regexps_items = [
        re.compile(r"^\s*(\d{1,3}\.)+\s*[a-zA-Zа-яА-ЯёЁ]"),
        re.compile(r"^\s*\d{1,3}(\)|\})"),

    ]  # 12
    regexps_subitem = [
        re.compile(r"^\s*[а-яё]\)"),
    ]
    quote_start = re.compile(r"^([\"'«])")
    quote_end = re.compile(r".*[\"'»][.;]?$")

    def __init__(self, text_features_only: bool = False) -> None:
        super().__init__()

        self.regexps_start = self.regexps_items + self.regexps_subitem + [self.roman_regexp]
        self.text_features_only = text_features_only

    def parameters(self) -> dict:
        return {"text_features_only": self.text_features_only}

    def fit(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> "LawTextFeatures":
        return self

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        assert len(documents) > 0

        result_matrix = pd.concat([self.__process_document(document) for document in documents], ignore_index=True)
        list_features = self.list_feature_extractor.transform(documents)
        result_matrix = pd.concat([result_matrix, list_features], axis=1)
        features = sorted(result_matrix.columns)
        return result_matrix[features].astype(float)

    def __process_document(self, lines: List[LineWithMeta], with_prev_next: bool = True) -> pd.DataFrame:

        page_ids = [line.metadata.page_id for line in lines]
        if page_ids:
            start_page, finish_page = min(page_ids), max(page_ids)
        else:
            start_page, finish_page = 0, 0

        features_df = pd.DataFrame(self._look_at_prev_line(document=lines, n=1))
        features_df["application"] = self._before_special_line(lines, self.__find_application)
        features_df["list_item"] = self._list_features(lines)

        one_line_features_dict = defaultdict(list)

        for line in lines:
            for item in self._one_line_features(line, total_lines=len(lines), start_page=start_page, finish_page=finish_page):
                feature_name, feature = item[0], item[1]
                one_line_features_dict[feature_name].append(feature)
        one_line_features_df = pd.DataFrame(one_line_features_dict)

        one_line_features_df["indentation"] = self._normalize_features(one_line_features_df.indentation)
        if not self.text_features_only:
            one_line_features_df["font_size"] = self._normalize_features(one_line_features_df.font_size)

        if with_prev_next:
            one_line_features_df = self.prev_next_line_features(one_line_features_df, 3, 3)
        result_matrix = pd.concat([one_line_features_df, features_df], axis=1)

        """for feature in result_matrix.keys():
            result_matrix[feature] = self._normalize_features(result_matrix[feature])"""
        return result_matrix

    def _look_at_prev_line(self, document: List[LineWithMeta], n: int = 1) -> Dict[str, List]:
        """
        looks at previous line and compare with current line
        @param document: list of lines
        @param n: previous line number to look
        @return: dict of features
        """
        res = defaultdict(list)
        lines_from_named = 0
        for line_id, line in enumerate(document):
            for regexp in self.named_regexp:
                if regexp.match(line.line.strip()):
                    lines_from_named = 0
            res["lines_from_named"].append(lines_from_named)
            lines_from_named += 1

            if line_id >= n:
                prev_line = document[line_id - n]
                is_prev_line_ends = prev_line.line.endswith((".", ";"))
                res["prev_line_ends"].append(1 if is_prev_line_ends else 0)
                res["prev_ends_with_colon"].append(prev_line.line.endswith(":"))
                res["prev_starts_with_article"].append(prev_line.line.lower().strip().startswith("статья"))
                res["prev_is_space"].append(prev_line.line.lower().isspace())
            else:
                res["prev_line_ends"].append(0)
                res["prev_ends_with_colon"].append(0)
                res["prev_starts_with_article"].append(0)
                res["prev_is_space"].append(0)
        return res

    def _one_line_features(self, line: LineWithMeta, total_lines: int, start_page: int, finish_page: int) -> Iterator[Tuple[str, int]]:
        yield "indentation", self._get_indentation(line)
        if not self.text_features_only:
            yield "page_id", normalization_by_min_max(line.metadata.page_id, min_v=start_page, max_v=finish_page)
            yield "bold", self._get_bold(line)
            yield "font_size", self._get_size(line)

        yield "line_id", normalization_by_min_max(line.metadata.line_id, min_v=0, max_v=total_lines)
        yield "num_year_regexp", len(regexps_year.findall(line.line))
        yield "endswith_dot", float(line.line.strip().endswith("."))
        yield "endswith_semicolon", float(line.line.strip().endswith(";"))
        yield "endswith_colon", float(line.line.strip().endswith(":"))
        yield "endswith_comma", float(line.line.strip().endswith(","))
        yield "startswith_bracket", float(line.line.strip().startswith(("(", "{")))

        bracket_cnt = 0
        for char in line.line:
            if char == "(":
                bracket_cnt += 1
            elif char == ")":
                bracket_cnt = max(0, bracket_cnt - 1)
        yield "bracket_num", bracket_cnt

        if self.roman_regexp.match(line.line) and len(line.line.strip()) > 3:
            yield "roman_regexp", 1
        else:
            yield "roman_regexp", 0

        yield ("startswith_quote", 1) if line.line.strip().startswith(('"', "'", "«")) else ("startswith_quote", 0)
        text_lower = line.line.lower()
        if "настоящей" in text_lower or "настоящего" or "пункта" in text_lower:
            yield "current_regexp", 1
        else:
            yield "current_regexp", 0
        yield ("year_regexp", 1) if "год" in text_lower else ("year_regexp", 0)

        # feature of application start
        if self.regexp_application_begin.match(text_lower.strip()):
            yield "regexp_application_begin", 1
        else:
            yield "regexp_application_begin", 0

        yield from self._start_regexp(line.line, self.named_regexp, "named")
        yield from self._start_regexp(line.line.lower(), self.regexps_items, "item")
        yield from self._start_regexp(line.line.lower(), self.regexps_subitem, "subitem")

        for regexp in self.regexps_subitem:
            match = regexp.match(line.line)
            if match:
                yield "subitem_regexp_len", len(match.group())
                yield "subitem_regexp_num", ord(match.group().strip()[:-1]) - ord("а")
            else:
                yield "subitem_regexp_len", 0
                yield "subitem_regexp_num", 0

        strip_text = line.line.strip()
        line_length = len(strip_text) + 1
        yield "supper_percent", sum((1 for letter in strip_text if letter.isupper())) / line_length
        yield "letter_percent", sum((1 for letter in strip_text if letter.isalpha())) / line_length
        yield "number_percent", sum((1 for letter in strip_text if letter.isnumeric())) / line_length
        yield "is_capitalized", 1.0 if len(strip_text) > 0 and strip_text[0].isupper() else 0.0

    def __find_body(self, document: List[LineWithMeta]) -> Optional[Tuple[int, int, int]]:
        for line_id, line in enumerate(document):
            text = "".join(filter(str.isalpha, line.line))
            if list(self._start_regexp(text, self.regexps_start + self.named_regexp))[-1] > 0:
                return line.metadata.page_id, line.metadata.line_id, line_id
        return None

    def __find_application(self, document: List[LineWithMeta]) -> Optional[Tuple[int, int, int]]:
        for line_id, line in enumerate(document):
            if self.regexp_application_begin.match(line.line.lower().strip()):
                return line.metadata.page_id, line.metadata.line_id, line_id
        return None

    def _inside_quotes(self, lines: List[LineWithMeta]) -> List[int]:
        quote_started = False
        quote_end = self.quote_end
        result = []
        new_quote = []
        for line in lines:
            text = line.line.strip()
            if quote_started:
                new_quote.append(1)
                if quote_end.match(text):  # quotation ended
                    quote_started = False
                    result.extend(new_quote)
                    new_quote = []
            else:
                match = self.quote_start.match(text)
                if match is not None and self.__any_item_found(text[1:]):  # quotation started
                    match = "»" if match.group() == "«" else match.group()
                    quote_end = re.compile(rf".*{match}[.;]?$")
                    if quote_end.match(text) is None:
                        quote_started = True
                        new_quote.append(1)
                    else:
                        result.append(1)
                else:
                    result.append(0)
        if quote_started:
            result.extend([0] * len(new_quote))
        return result

    def __any_item_found(self, text: str) -> bool:
        regexps = self.regexps_start + self.named_regexp
        for regexp in regexps:
            if regexp.match(text):
                return True
        return False
