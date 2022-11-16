import gzip
import os
import pickle
from abc import ABC
from typing import Tuple

from xgboost import XGBClassifier

from dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier


class AbstractPickledLineTypeClassifier(AbstractLineTypeClassifier, ABC):

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def load(self, path: str) -> Tuple[XGBClassifier, dict]:
        path = os.path.abspath(path)
        with gzip.open(path) as file:
            classifier, feature_extractor_parameters = pickle.load(file)
        return classifier, feature_extractor_parameters

    def save(self, path_out: str, parameters: object) -> str:
        if path_out.endswith(".pkl"):
            path_out += ".gz"
        elif not path_out.endswith(".gz"):
            path_out += ".pkl.gz"

        with gzip.open(path_out, "wb") as file_out:
            pickle.dump(obj=parameters, file=file_out)
        return path_out
