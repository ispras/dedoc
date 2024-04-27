import gzip
import logging
import os
import pickle
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
import xgbfir
from xgboost import XGBClassifier

from dedoc.download_models import download_from_hub


class FintocClassifier:
    """
    Classifier of financial documents for the FinTOC 2022 Shared task (https://wp.lancs.ac.uk/cfie/fintoc2022/).
    Lines are classified in two stages:
        1. Binary classification title/not title (title detection task)
        2. Classification of title lines into title depth classes (1-6) (TOC generation task)

    More important lines have a lesser depth.
    As a result:
        1. For non-title lines, classifier returns -1.
        2. For title lines, classifier returns their depth (from 1 to 6).
    """

    def __init__(self, language: str, weights_dir_path: Optional[str] = None) -> None:
        """
        :param language: language of data ("en", "fr", "sp")
        :param weights_dir_path: path to directory with trained models weights
        """
        self.weights_dir_path = weights_dir_path
        self.language = language
        self.classifiers = {"binary": None, "target": None}

    def predict(self, features: pd.DataFrame) -> List[int]:
        """
        Two-staged classification: title/not title and depth classification for titles.
        For non-title lines, classifier returns -1, for title lines, classifier returns their depth (from 1 to 6).
        """
        binary_predictions = self.binary_classifier.predict(features)
        # binary_predictions = [True, False, ...], target predictions are predicted only for True items
        target_predictions = self.target_classifier.predict(features[binary_predictions])
        result = np.ones_like(binary_predictions) * -1
        result[binary_predictions] = target_predictions
        # return list [1, 2, 3, -1, -1, ...], where positive values mean headers depth, -1 mean non-header lines
        return list(result)

    def fit(self,
            binary_classifier_parameters: Dict[str, Union[int, float, str]],
            target_classifier_parameters: Dict[str, Union[int, float, str]],
            features: pd.DataFrame,
            features_names: List[str]) -> None:
        self.classifiers["binary"] = XGBClassifier(**binary_classifier_parameters)
        self.classifiers["target"] = XGBClassifier(**target_classifier_parameters)
        self.binary_classifier.fit(features[features_names], features.label != -1)
        self.target_classifier.fit(features[features_names][features.label != -1], features.label[features.label != -1])

    def save(self, classifiers_dir_path: str, features_importances_dir_path: str, logger: logging.Logger, features_names: List[str], reader: str) -> None:
        os.makedirs(classifiers_dir_path, exist_ok=True)
        for classifier_type in ("binary", "target"):
            with gzip.open(os.path.join(classifiers_dir_path, f"{classifier_type}_classifier_{self.language}_{reader}.pkg.gz"), "wb") as output_file:
                pickle.dump(self.classifiers[classifier_type], output_file)
        logger.info(f"Classifiers were saved in {classifiers_dir_path} directory")

        os.makedirs(features_importances_dir_path, exist_ok=True)
        for classifier_type in ("binary", "target"):
            xgbfir.saveXgbFI(self.classifiers[classifier_type], feature_names=features_names,
                             OutputXlsxFile=os.path.join(features_importances_dir_path, f"feature_importances_{classifier_type}_{self.language}_{reader}.xlsx"))
        logger.info(f"Features importances were saved in {features_importances_dir_path} directory")

    @property
    def binary_classifier(self) -> XGBClassifier:
        return self.__lazy_load_weights("binary")

    @property
    def target_classifier(self) -> XGBClassifier:
        return self.__lazy_load_weights("target")

    def __lazy_load_weights(self, classifier_type: str) -> XGBClassifier:
        if self.classifiers[classifier_type] is None:
            assert self.weights_dir_path is not None
            file_name = f"{classifier_type}_classifier_{self.language}.pkg.gz"
            classifier_path = os.path.join(self.weights_dir_path, file_name)
            if not os.path.isfile(classifier_path):
                download_from_hub(out_dir=self.weights_dir_path,
                                  out_name=file_name,
                                  repo_name="fintoc_classifiers",
                                  hub_name=f"{classifier_type}_classifier_{self.language}_txt_layer.pkg.gz")

            with gzip.open(classifier_path, "rb") as input_file:
                self.classifiers[classifier_type] = pickle.load(file=input_file)

        return self.classifiers[classifier_type]
