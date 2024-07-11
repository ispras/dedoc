import json
import logging
import os
import tempfile
import zipfile
from abc import ABC
from typing import Optional, Tuple

from xgboost import XGBClassifier

from dedoc.download_models import download_from_hub
from dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier import AbstractLineTypeClassifier
from dedoc.utils.parameter_utils import get_param_gpu_available


class AbstractPickledLineTypeClassifier(AbstractLineTypeClassifier, ABC):
    """
    Abstract class for lines classification with functionality of loading and saving a classifier.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.logger = self.config.get("logger", logging.getLogger())

    def load(self, classifier_type: str, path: str) -> Tuple[XGBClassifier, dict]:
        """
        Load the pickled classifier with parameters for a feature extractor.

        :param classifier_type: name of the classifier to load from huggingface in case `path` does not exist
            (https://huggingface.co/dedoc/line_type_classifiers)
        :param path: path from where to load the pickled classifier
        :return: loaded XGBClassifier and parameters for a feature extractor
        """
        if not os.path.isfile(path):
            out_dir, out_name = os.path.split(path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="line_type_classifiers", hub_name=f"{classifier_type}.zip")

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(path) as archive:
                archive.extractall(tmpdir)

            with open(os.path.join(tmpdir, "parameters.json")) as parameters_file:
                feature_extractor_parameters = json.load(parameters_file)
            classifier = XGBClassifier()
            classifier.load_model(os.path.join(tmpdir, "classifier.json"))

        if get_param_gpu_available(self.config, self.logger):
            gpu_params = dict(predictor="gpu_predictor", tree_method="auto", gpu_id=0)
            classifier.set_params(**gpu_params)
            classifier.get_booster().set_param(gpu_params)

        return classifier, feature_extractor_parameters

    @staticmethod
    def save(path_out: str, classifier: XGBClassifier, parameters: dict) -> str:
        """
        Save the classifier (with initialization parameters for a feature extractor) into the `.zip` file with path=`path_out`

        * classifier -> classifier.json
        * parameters -> parameters.json

        :param path_out: path (with file name) where to save the object
        :param classifier: classifier to save
        :param parameters: feature extractor parameters to save
        :return: the resulting path of the saved file
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            clf_path = os.path.join(tmpdir, "classifier.json")
            params_path = os.path.join(tmpdir, "parameters.json")
            classifier.save_model(clf_path)
            with open(params_path, "w") as out_file:
                json.dump(parameters, out_file)

            with zipfile.ZipFile(path_out, "w") as archive:
                archive.write(clf_path, os.path.basename(clf_path))
                archive.write(params_path, os.path.basename(params_path))
        return path_out
