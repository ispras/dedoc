from typing import Iterable, List, Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.utils.utils import flatten


class FirstWordFeatures(AbstractFeatureExtractor):

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer()

    def parameters(self) -> dict:
        return {"vectorizer": self.vectorizer}

    def fit(self, lines: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> "FirstWordFeatures":
        first_word = self.__get_first_word(flatten(lines))
        self.vectorizer.fit(first_word)
        return self

    def transform(self, lines: List[List[LineWithMeta]], y: Optional[List[str]] = None) -> pd.DataFrame:
        first_word = self.__get_first_word(flatten(lines))
        return self.prev_next_line_features(self.vectorizer.transform(first_word).toarray(), 1, 1)

    def __get_first_word(self, lines: Iterable[LineWithMeta]) -> List[str]:
        res = []
        for line in lines:
            splitted = line.line.strip().split()
            text = splitted[0] if len(splitted) > 0 else ""
            res.append(text)
        return res
