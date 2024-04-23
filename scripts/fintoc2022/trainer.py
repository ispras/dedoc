import hashlib
import json
import logging
import os
import shutil
from statistics import mean
from typing import Optional

import pandas as pd
from sklearn.model_selection import GroupKFold
from tqdm import tqdm

from dedoc.structure_extractors.concrete_structure_extractors.fintoc_structure_extractor import FintocStructureExtractor
from dedoc.structure_extractors.feature_extractors.fintoc_feature_extractor import FintocFeatureExtractor
from dedoc.structure_extractors.line_type_classifiers.fintoc_classifier import FintocClassifier
from dedoc.utils.utils import flatten
from scripts.fintoc2022.dataset_loader import FintocDatasetLoader
from scripts.fintoc2022.metric import score
from scripts.fintoc2022.utils import create_json_result, get_values_from_csv


class FintocTrainer:
    """
    Class to train and evaluate classifiers for the FinTOC 2022 Shared task (https://wp.lancs.ac.uk/cfie/fintoc2022/).
    The code is a modification of the winner's solution (ISP RAS team).
    """
    def __init__(self,
                 data_url: str,
                 logger: logging.Logger,
                 language: str,
                 classifiers_dir_path: str,
                 scores_dir_path: str,
                 features_importances_dir_path: str,
                 tmp_dir: str,
                 binary_classifier_parameters: dict = None,
                 target_classifier_parameters: dict = None,
                 n_splits: int = 3) -> None:
        """
        :param data_url: url to download training data for FintocDatasetLoader
        :param logger: logger for logging details of classifier training
        :param language: language of data ("en", "fr", "sp")
        :param classifiers_dir_path: path to the directory where to save trained classifiers
        :param scores_dir_path: path to the directory where to save final scores during cross-validation
        :param features_importances_dir_path: path to the directory where to save XLSX files with information about most important features for classifiers
        :param tmp_dir: path to temporary directory for saving the dataset and output json files with predictions
        :param binary_classifier_parameters: parameters to pass to xgboost.XGBClassifier for classification header/non-header
        :param target_classifier_parameters: parameters to pass to xgboost.XGBClassifier for lines depth classification
        :param n_splits: number of splits for cross-validation
        """
        self.logger = logger
        self.language = language
        self.feature_extractor = FintocFeatureExtractor()
        self.structure_extractor = FintocStructureExtractor()

        self.binary_classifier_parameters = {} if binary_classifier_parameters is None else binary_classifier_parameters
        self.target_classifier_parameters = {} if target_classifier_parameters is None else target_classifier_parameters
        self.classifier = FintocClassifier(language=self.language)

        self.tmp_dir = tmp_dir
        os.makedirs(self.tmp_dir, exist_ok=True)
        self.scores_dir_path = scores_dir_path
        self.features_importances_dir_path = features_importances_dir_path
        self.classifiers_dir_path = classifiers_dir_path

        self.data_url = data_url
        url_hash = hashlib.md5(self.data_url.encode()).hexdigest()
        self.dataset_dir = os.path.join(self.tmp_dir, f"dataset_{url_hash}")
        self.data_loader = FintocDatasetLoader(dataset_dir=self.dataset_dir, logger=logger)

        self.n_splits = n_splits
        self.additional_features_fields = ("line", "label", "group", "uid")

    def fit(self, reader_name: str, cross_val: bool = True, use_cache: bool = True) -> None:
        """
        1 - Load data by `self.data_url` if needed, extract lines from PDF by chosen reader by `reader_name` if needed (FintocDatasetLoader).
        2 - Extract a feature matrix for extracted document lines (FintocFeatureExtractor).
        3 - Do a cross-validation if needed.
        4 - Train resulting classifiers (binary, target) and save them to `self.classifiers_dir_path` (FintocClassifier).

        :param reader_name: ("tabby", "txt_layer") - type of reader for lines extraction from PDF
        :param cross_val: whether to do cross-validation or not
        :param use_cache: whether to use cached extracted lines as training data
        """
        # obtain training data
        self.logger.info("Get data for training and evaluation")
        data = self.data_loader.get_data(language=self.language, reader_name=reader_name, use_cache=use_cache)

        # create feature matrix
        self.logger.info("Create a feature matrix")
        features, documents = self.structure_extractor.get_features(documents_dict=data)
        self.logger.info(f"Features shape: {features.shape}")
        for feature_field in self.additional_features_fields:
            features[feature_field] = [getattr(line, feature_field) for line in flatten(documents)]
        features["label"] = features["label"].astype(int)
        features_names = self.__get_features_names(features)

        # cross-validation using fintoc metric
        gt_dir = os.path.join(self.dataset_dir, "data", self.language, "annots")
        scores = self.__cross_validate(features=features, gt_dir=gt_dir) if cross_val else None

        # train resulting classifiers on all data
        self.logger.info("Train resulting classifiers")
        self.classifier.fit(self.binary_classifier_parameters, self.target_classifier_parameters, features=features, features_names=features_names)
        self.__save(features_names=features_names, scores=scores)

    def __get_features_names(self, features_df: pd.DataFrame) -> list:
        features_names = [col for col in features_df.columns if col not in self.additional_features_fields]
        return features_names

    def __cross_validate(self, features: pd.DataFrame, gt_dir: str) -> dict:
        self.logger.info("Start cross-validation")
        features_names = self.__get_features_names(features)
        results_path = os.path.join(self.scores_dir_path, "cross_val_results", self.language)
        os.makedirs(results_path, exist_ok=True)

        kf = GroupKFold(n_splits=self.n_splits)
        json_results_dir = os.path.join(self.tmp_dir, "json_results", self.language)

        result_scores = {"td_scores": [], "toc_scores": []}
        for i, (train_index, val_index) in tqdm(enumerate(kf.split(features, groups=features.group)), total=self.n_splits):
            df_train = features.loc[train_index]
            df_val = features.loc[val_index]
            self.classifier.fit(self.binary_classifier_parameters, self.target_classifier_parameters, features=df_train, features_names=features_names)
            predicted_classes = self.classifier.predict(df_val[features_names])
            result_dict = create_json_result(df_val, predicted_classes)

            if os.path.isdir(json_results_dir):
                shutil.rmtree(json_results_dir)
            os.makedirs(json_results_dir)

            tmp_gt_dir, predictions_dir = os.path.join(json_results_dir, "groundtruth"), os.path.join(self.tmp_dir, "predictions")
            os.makedirs(tmp_gt_dir)
            os.makedirs(predictions_dir)

            for doc_name, result in result_dict.items():
                gt_doc_name = doc_name + ".pdf.fintoc4.json"
                if gt_doc_name not in os.listdir(gt_dir):
                    self.logger.warning(f"{gt_doc_name} is not found in groundtruth")
                    continue
                with open(os.path.join(predictions_dir, gt_doc_name), "w") as json_file:
                    json.dump(result, json_file, indent=2)
                shutil.copy(os.path.join(gt_dir, gt_doc_name), os.path.join(tmp_gt_dir, gt_doc_name))
            score(tmp_gt_dir, predictions_dir)

            path_scores = os.path.join(results_path, str(i))
            os.makedirs(path_scores, exist_ok=True)
            for file_name in ["td.log", "toc.log", "td_report.csv", "toc_report.csv"]:
                shutil.move(file_name, os.path.join(path_scores, file_name))

            f1, inex_f1 = get_values_from_csv(path_scores)
            result_scores["td_scores"].append(f1)
            result_scores["toc_scores"].append(inex_f1)
            self.logger.info(f'Iteration {i}:\ntd={result_scores["td_scores"][-1]}\ntoc={result_scores["toc_scores"][-1]}')

        result_scores["td_mean"] = mean(result_scores["td_scores"])
        result_scores["toc_mean"] = mean(result_scores["toc_scores"])
        return result_scores

    def __save(self, features_names: list[str], scores: Optional[dict]) -> None:

        if scores is not None:
            os.makedirs(self.scores_dir_path, exist_ok=True)
            scores_path = os.path.join(self.scores_dir_path, f"scores_{self.language}.json")
            with open(scores_path, "w") as f:
                json.dump(scores, f)
            self.logger.info(f"Scores were saved in {scores_path}")

        self.classifier.save(
            classifiers_dir_path=self.classifiers_dir_path,
            features_importances_dir_path=self.features_importances_dir_path,
            features_names=features_names,
            logger=self.logger
        )
