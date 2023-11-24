import gzip
import logging
import os
import pickle
from abc import ABC
from typing import Tuple

from xgboost import XGBClassifier


from dedoc.download_models import download_from_hub
from dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier
from dedoc.utils.parameter_utils import get_param_gpu_available


class AbstractPickledLineTypeClassifier(AbstractLineTypeClassifier, ABC):

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.logger = self.config.get("logger", logging.getLogger())

    def load(self, classifier_type: str, path: str) -> Tuple[XGBClassifier, dict]:
        if not os.path.isfile(path):
            out_dir, out_name = os.path.split(path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="line_type_classifiers", hub_name=f"{classifier_type}.pkl.gz")

        with gzip.open(path) as file:
            classifier, feature_extractor_parameters = pickle.load(file)

        if get_param_gpu_available(self.config, self.logger):
            gpu_params = dict(predictor="gpu_predictor", tree_method="auto", gpu_id=0)
            classifier.set_params(**gpu_params)
            classifier.get_booster().set_param(gpu_params)

        return classifier, feature_extractor_parameters

    def save(self, path_out: str, parameters: object) -> str:
        if path_out.endswith(".pkl"):
            path_out += ".gz"
        elif not path_out.endswith(".gz"):
            path_out += ".pkl.gz"

        with gzip.open(path_out, "wb") as file_out:
            pickle.dump(obj=parameters, file=file_out)
        return path_out
