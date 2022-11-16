import json
from abc import ABC, abstractmethod
from typing import List, Pattern, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats._multivariate import method

from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.color_annotation import ColorAnnotation
from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import \
    regexps_number, regexps_ends_of_number, regexps_subitem_extended, regexps_subitem, regexps_year
from dedoc.utils.utils import list_get


class AbstractFeatureExtractor(ABC):
    number_regexp = regexps_number
    ends_of_number = regexps_ends_of_number
    item_regexp = regexps_subitem
    item_extended_regexp = regexps_subitem_extended
    year_regexp = regexps_year

    @abstractmethod
    def parameters(self) -> dict:
        pass

    @abstractmethod
    def fit(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> "AbstractFeatureExtractor":
        pass

    @abstractmethod
    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        pass

    def fit_transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        self.fit(documents, y)
        return self.transform(documents)

    @staticmethod
    def _prev_line_features(feature_matrix: np.ndarray, n: int) -> np.ndarray:
        """
        @param feature_matrix: matrix where rows are lines, columns are features
        @return: feature matrix where lines were shifted on n lines
        """
        if n > feature_matrix.shape[0]:
            return np.zeros(feature_matrix.shape)
        return np.vstack((np.zeros((n, feature_matrix.shape[1])), feature_matrix[:-n, :]))

    @staticmethod
    def _next_line_features(feature_matrix: np.ndarray, n: int) -> np.ndarray:
        if n > feature_matrix.shape[0]:
            return np.zeros(feature_matrix.shape)
        return np.vstack((feature_matrix[n:, :], np.zeros((n, feature_matrix.shape[1]))))

    @staticmethod
    def _create_features_name(old_names: pd.Index, which: str, num: int) -> List[str]:
        return ["{}_{}_{}".format(old_name, which, num) for old_name in old_names]

    def prev_next_line_features(self, matrix: pd.DataFrame, n_prev: int, n_next: int) -> pd.DataFrame:
        """
        add previous and next features with their names
        """
        feature_names = matrix.columns
        prev_line_features = [pd.DataFrame(data=self._prev_line_features(matrix.values, i),
                                           columns=self._create_features_name(feature_names, "prev", i))
                              for i in range(1, n_prev + 1)]
        next_line_features = [pd.DataFrame(data=self._next_line_features(matrix.values, i),
                                           columns=self._create_features_name(feature_names, "next", i))
                              for i in range(1, n_next + 1)]

        matrices = [matrix] + prev_line_features + next_line_features
        result_matrix = pd.concat(matrices, axis=1)
        return result_matrix

    def _start_regexp(self, line: str, regexps: List[Pattern],
                      suffix: Optional[str] = None) -> Iterable[Tuple[str, float]]:
        matches = 0
        text = line.strip()
        for i, pattern in enumerate(regexps):  # list patterns
            if suffix is None:
                feature_name = "start_regexp_{}".format(i)
            else:
                feature_name = "start_regexp_{}_{}".format(i, suffix)
            match = pattern.match(text)
            if match is not None and match.end() > 0:
                matches += 1
                yield feature_name, match.end() - match.start()
            else:
                yield feature_name, 0
        if suffix is None:
            yield "start_regexp_num_matches", matches
        else:
            yield "start_regexp_num_matches_{}".format(suffix), matches

    @staticmethod
    def _get_size(line: LineWithMeta) -> float:
        sizes = [annotation for annotation in line.annotations if annotation.name == SizeAnnotation.name]  # font size
        return float(sizes[0].value) if len(sizes) > 0 else 0.

    @staticmethod
    def _get_bold(line: LineWithMeta) -> float:
        bold = [annotation for annotation in line.annotations
                if annotation.name == BoldAnnotation.name and annotation.value == "True"]
        return 1. if len(bold) > 0 else 0

    @staticmethod
    def _get_bold_percent(line: LineWithMeta) -> float:
        bold_character_number = sum([annotation.end - annotation.start for annotation in line.annotations
                                     if annotation.name == BoldAnnotation.name and annotation.value == "True"])
        if len(line.line) == 0:
            return 0
        return bold_character_number / len(line.line)

    @staticmethod
    def _is_first_bold(line: LineWithMeta) -> float:
        for annotation in line.annotations:
            if annotation.name == BoldAnnotation.name and annotation.value == "True" and annotation.start == 0:
                return 1.
        return 0

    @staticmethod
    def _get_italic(line: LineWithMeta) -> float:
        italic = [annotation for annotation in line.annotations if annotation.name == ItalicAnnotation.name]
        return 1. if len(italic) > 0 else 0

    @staticmethod
    def _get_underlined(line: LineWithMeta) -> float:
        underlined = [annotation for annotation in line.annotations if annotation.name == UnderlinedAnnotation.name]
        return 1. if len(underlined) > 0 else 0

    @staticmethod
    def _get_color(line: LineWithMeta) -> Iterable[Tuple[str, float]]:
        color = [annotation for annotation in line.annotations if annotation.name == ColorAnnotation.name]
        if len(color) == 0:
            value = {}
        else:
            value = json.loads(color[0].value)
        red = value.get("red", 0)
        green = value.get("green", 0)
        blue = value.get("blue", 0)
        yield "red", red
        yield "green", green
        yield "blue", blue
        mean = (red + green + blue) / 3
        yield "color_dispersion", sum([(c - mean) ** 2 for c in (red, green, blue)]) / 2

    @staticmethod
    def _get_spacing(line: LineWithMeta) -> float:
        spacing = [annotation for annotation in line.annotations if annotation.name == SpacingAnnotation.name]
        return float(spacing[0].value) if len(spacing) > 0 else -1

    @staticmethod
    def _get_indentation(line: LineWithMeta) -> float:
        indentation = [annotation for annotation in line.annotations if isinstance(annotation, IndentationAnnotation)]
        return float(indentation[0].value) if len(indentation) > 0 else 0

    @staticmethod
    def _can_be_prev_element(this_item: Optional[str], prev_item: Optional[str]) -> bool:
        """
        check if prev_item can be the previous element of this item in the correct list
        For example "2" can be previous element of "3", "2.1." can be previous element of "2.1.1"
        If prev_item is None then this_item is the first item in the list and should be 1
        @return:
        """
        if this_item is None:
            return False
        this_item_list = [i for i in this_item.split(".") if len(i) > 0]
        if this_item_list == ["1"]:
            return True
        if prev_item is None:
            return False
        prev_item_list = [i for i in prev_item.split(".") if len(i) > 0]
        if len(prev_item_list) > len(this_item_list):
            return False
        if len(prev_item_list) < len(this_item_list) - 1:
            return False
        this_item_prefix = this_item_list[:-1]
        prev_item_prefix = prev_item_list[:-1]
        if len(prev_item_list) == len(this_item_list) - 1:
            return prev_item_list == this_item_prefix and this_item_list[-1] == "1"
        if len(prev_item_list) == len(this_item_list):
            return prev_item_prefix == this_item_prefix and int(this_item_list[-1]) - int(prev_item_list[-1]) == 1
        raise Exception("Unexpected case where this_item = {} prev_item = {}".format(this_item, prev_item))

    def _before_special_line(self, document: List[LineWithMeta], find_special_line: method) -> List[float]:
        """
        @param document: document in form of list of lines
        @param find_special_line: function that find some special line, see __find_toc for example
        @return: list of distances from given line to first special line. If line lay before the special line, then
        distance is negative, if line lay after special line then distance is positive, for special line distance is 0
        If there is no special line in the document then distance is 0 for every line
        """
        result = []
        special_line_position = find_special_line(document)
        if special_line_position is None:
            result.extend([0. for _ in document])
        else:
            special_line_id = special_line_position[-1]
            for line_id, line in enumerate(document):
                result.append(line_id - special_line_id)
        return result

    def _list_features(self, lines: List[LineWithMeta]) -> List[float]:
        previous_ids = [-1]
        texts = [line.line.strip().strip() for line in lines]
        matches = map(self.number_regexp.match, texts)
        numbers = [(line_id, match.group().strip()) for line_id, match in enumerate(matches) if match]

        for num, (line_id, number) in enumerate(numbers):
            searched = self.ends_of_number.search(number)
            if searched is not None:
                numbers[num] = (line_id, number[:searched.start()])
            if number.endswith((')', '}', '.')):
                numbers[num] = (line_id, number[:-1])

        if len(numbers) == 0:
            return [0 for _ in lines]
        line_ids, numbers = zip(*numbers)

        result_numbers = []
        for i in range(len(numbers)):
            one_item = []
            this_item = numbers[i]
            for k in previous_ids:
                prev_item = list_get(numbers, i + k)
                one_item.append(1 if self._can_be_prev_element(this_item=this_item, prev_item=prev_item) else -1)
            one_item = max(one_item)
            result_numbers.append(one_item)
        result = [0 for _ in lines]
        for line_id, one_item in zip(line_ids, result_numbers):
            result[line_id] = one_item
        return result

    @staticmethod
    def _get_features_quantile(feature_column: pd.Series) -> pd.Series:
        """
        @param feature_column: column with one feature
        @return: column with feature's quantiles
        """
        feature_column = feature_column.fillna(feature_column.min() - 1)
        feature_column_s = np.sort(feature_column)
        feature_quantiles = np.searchsorted(feature_column_s, feature_column, "left")
        feature_quantiles += np.searchsorted(feature_column_s, feature_column, "right")
        feature_quantiles = feature_quantiles / 2 / feature_column.shape[0]
        return pd.Series(feature_quantiles)

    @staticmethod
    def _normalize_features(feature_column: pd.Series) -> pd.Series:
        """
        new_feature = (feature - mean) / (max - min) if max = min else 0
        Output: normalized feature vector  [-1; 1]
        """
        feature_mean, feature_min, feature_max = feature_column.mean(), feature_column.min(), feature_column.max()
        new_feature_column = (feature_column - feature_mean) / (feature_max - feature_min) if \
            feature_max - feature_min != 0.0 else 0.0
        return new_feature_column
