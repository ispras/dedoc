from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_prefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bullet_prefix import BulletPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.letter_prefix import LetterPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class Window:
    def __init__(self, indent_std: float, prefix_before: List[LinePrefix], prefix_after: List[LinePrefix]) -> None:
        self.indent_std = indent_std
        self.prefix_before = prefix_before
        self.prefix_after = prefix_after


class ListFeaturesExtractor(AbstractFeatureExtractor):
    """
    Extracts features for list items:
        - indentation of items is analysed (same/different)
        - prefixes of items are analysed, if items can be predecessors of others

    The analysis is executed in a window of a fixed size (size of window = number of neighbor lines)
    """

    def __init__(self, window_size: int = 25, prefix_list: Optional[List[LinePrefix]] = None) -> None:
        super().__init__()
        self.window_size = window_size
        self.prefix_list = prefix_list if prefix_list is not None else [BulletPrefix, LetterPrefix, BracketPrefix, DottedPrefix]

    def parameters(self) -> dict:
        return {"window_size": self.window_size}

    def fit(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> "AbstractFeatureExtractor":
        return self

    def transform(self, documents: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        features = [self.one_document(doc)[1] for doc in documents]
        return pd.concat(features, axis=0, ignore_index=True)

    def one_document(self, doc: List[LineWithMeta]) -> Tuple[List[LinePrefix], pd.DataFrame]:
        prefixes = [self._get_prefix(line) for line in doc]
        indents = np.array([prefix.indent for prefix in prefixes])
        res = []
        doc_size = len(prefixes)
        for line_id, (_line, prefix) in enumerate(zip(doc, prefixes)):
            window = self._get_window(indents=indents, prefixes=prefixes, line_id=line_id, doc_size=doc_size)
            features = self._one_line_features(window=window, prefix=prefix)
            res.append(features)
        features_dict = defaultdict(list)
        for features in res:
            for feature_name, feature_value in features.items():
                features_dict[feature_name].append(feature_value)
        return prefixes, pd.DataFrame(features_dict)

    def _one_line_features(self, prefix: LinePrefix, window: Window) -> Dict[str, float]:
        predecessor_num = 0
        predecessor_num_same_indent = 0
        same_indent = 0
        same_prefix = 0
        for prefix_other in window.prefix_before + window.prefix_after:
            is_predecessor = prefix.predecessor(prefix_other) or prefix.successor(prefix_other)
            is_same_indent = self._same_indent(this_indent=prefix.indent, other_indent=prefix_other.indent, std=window.indent_std)
            predecessor_num += is_predecessor
            same_indent += is_same_indent
            predecessor_num_same_indent += (is_same_indent and is_predecessor)
            same_prefix += (prefix_other.name == prefix.name)

        window_size = len(window.prefix_before) + len(window.prefix_after) + 1
        same_indent /= window_size
        predecessor_num_same_indent /= window_size
        predecessor_num /= window_size
        return {
            f"same_indent_{self.window_size}": same_indent,
            f"predecessor_num_same_indent_{self.window_size}": predecessor_num_same_indent,
            f"predecessor_num_{self.window_size}": predecessor_num
        }

    def _same_indent(self, this_indent: float, other_indent: float, std: float) -> bool:
        eps = 1
        return abs(this_indent - other_indent) <= 0.1 * std + eps

    def _get_prefix(self, line: LineWithMeta) -> LinePrefix:
        return get_prefix(self.prefix_list, line)

    def _get_window(self, indents: np.ndarray, prefixes: List[LinePrefix], line_id: int, doc_size: int) -> Window:
        assert line_id < doc_size
        left = max(line_id - self.window_size, 0)
        right = min(line_id + self.window_size, doc_size)
        indents = indents[left: right]
        prefix_before = prefixes[left: line_id]
        prefix_after = prefixes[line_id + 1: right]
        return Window(indent_std=indents.std(), prefix_before=prefix_before, prefix_after=prefix_after)
