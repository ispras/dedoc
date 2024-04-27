import json
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy.stats._multivariate import method

from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.utils.utils import flatten


class PairedFeatureExtractor(AbstractFeatureExtractor):
    """
    This class is used as an auxiliary feature extractor to the main extractor.
    It allows to add "raw" features related to the lines importance.
    Based on one line property (size, indentation) it computes a raw line's depth inside the document tree.

    Example:
        For lines
            line1 (size=16)
            line2 (size=14)
            line3 (size=12)
            line4 (size=12)
            line5 (size=14)
            line6 (size=12)
        We will obtain a feature vector (raw_depth_size)
            [0, 1, 2, 2, 1, 2]
    """

    def parameters(self) -> dict:
        return {}

    def fit(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> "AbstractFeatureExtractor":
        return self

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        df = pd.DataFrame()
        df["raw_depth_size"] = list(flatten([self._handle_one_document(document, self.__get_size) for document in documents]))
        df["raw_depth_indentation"] = list(flatten([self._handle_one_document(document, self._get_indentation) for document in documents]))
        return df

    def _handle_one_document(self, document: List[LineWithMeta], get_feature: method) -> List[int]:
        if len(document) == 0:
            return []
        if len(document) == 1:
            return [0]

        features = [get_feature(line) for line in document]
        std = np.std(features)
        result = []
        stack = []

        for line in document:
            while len(stack) > 0 and self.__compare_lines(stack[-1], line, get_feature, std) <= 0:  # noqa
                stack.pop()
            result.append(len(stack))
            stack.append(line)

        return result

    def __get_size(self, line: LineWithMeta) -> float:
        annotations = line.annotations
        size_annotation = [annotation for annotation in annotations if annotation.name == SizeAnnotation.name]
        if len(size_annotation) > 0:
            return float(size_annotation[0].value)

        bbox_annotation = [annotation for annotation in annotations if annotation.name == BBoxAnnotation.name]
        if len(bbox_annotation) > 0:
            bbox = json.loads(bbox_annotation[0].value)
            return bbox["height"]

        return 0

    def __compare_lines(self, first_line: LineWithMeta, second_line: LineWithMeta, get_feature: method, threshold: float = 0) -> int:
        first_feature = get_feature(first_line)
        second_feature = get_feature(second_line)

        if first_feature > second_feature + threshold:
            return 1

        if second_feature > first_feature + threshold:
            return -1

        return 0
