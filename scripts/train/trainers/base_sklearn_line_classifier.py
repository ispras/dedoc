import abc
import gzip
import hashlib
import json
import logging
import os
import pickle
from collections import Counter, OrderedDict
from statistics import mean
from typing import Any, Callable, List, Optional

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold
from tqdm import tqdm
from xgboost import XGBClassifier

from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.utils.utils import flatten, identity
from scripts.train.trainers.data_loader import DataLoader
from scripts.train.trainers.dataset import LineClassifierDataset
from scripts.train.trainers.errors_saver import ErrorsSaver
from train_dataset.data_structures.line_with_label import LineWithLabel


class BaseClassifier(XGBClassifier):
    """
    Base class for a classifier.
    See documentation of `XGBClassifier <https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier>`_ to get more details.
    """
    def __init__(self, **kwargs: Any) -> None:  # noqa
        super().__init__(**kwargs)


class BaseSklearnLineClassifierTrainer:
    """
    Base class for training :class:`~scripts.train.trainers.base_sklearn_line_classifier.BaseClassifier`.
    It provides data loading and saving, classifier training and cross-validation.
    During cross-validation, classifier errors are saved into `errors` directory inside `tmp_dir`.
    """
    def __init__(self,
                 data_url: str,
                 logger: logging.Logger,
                 feature_extractor: AbstractFeatureExtractor,
                 path_out: str,
                 path_scores: Optional[str] = None,
                 path_features_importances: Optional[str] = None,
                 tmp_dir: Optional[str] = None,
                 train_size: float = 0.75,
                 classifier_parameters: dict = None,
                 label_transformer: Callable[[str], str] = None,
                 random_seed: int = 42,
                 get_sample_weight: Callable[[LineWithLabel], float] = None,
                 n_splits: int = 10,
                 *,
                 config: dict) -> None:
        """
        :param data_url: url to download training data for :class:`~scripts.train.trainers.data_loader.DataLoader`
        :param logger: logger for logging details of classifier training
        :param feature_extractor: feature extractor for making feature matrix from document lines
        :param path_out: full path (with filename) to save a trained model
        :param path_scores: full path to the JSON file to save the scores (accuracy) of a trained classifier (won't be saved if None)
        :param path_features_importances: full path to the XLSX file to save information about most important features for classifier (won't be saved if None)
        :param tmp_dir: path to the directory where to save downloaded training data and the classifier's errors, "/tmp" if None is provided
        :param train_size: proportion of the training data, value can be in the diapason (0;1) or (0;100)
        :param classifier_parameters: parameters for the classifier initialization
        :param label_transformer: function for mapping initial data labels into the labels for classifier training, labels identity if None is provided
        :param random_seed: seed for the classifier initialization
        :param get_sample_weight: function for `sample_weight` calculating: LineWithLabel->weight [0,1] for setting line importance during classifier training,
            LineWithLabel->1 if None is provided
        :param n_splits: number of data splits for cross-validation
        :param config: any custom configuration
        """
        self.data_url = data_url
        self.logger = logger
        self.feature_extractor = feature_extractor
        self.tmp_dir = "/tmp" if tmp_dir is None else tmp_dir
        url_hash = hashlib.md5(self.data_url.encode()).hexdigest()
        self.dataset_dir = os.path.join(self.tmp_dir, f"dataset_{url_hash}")
        self.data_loader = DataLoader(dataset_dir=self.dataset_dir, label_transformer=label_transformer, logger=logger, data_url=data_url, config=config)
        self.random_seed = random_seed
        self.get_sample_weight = get_sample_weight if get_sample_weight is not None else lambda t: 1
        os.makedirs(self.tmp_dir, exist_ok=True)
        assert train_size > 0
        assert train_size < 1 or 1 < train_size < 100
        self.train_size = train_size if train_size < 1 else train_size / 100
        self.classifier_parameters = {} if classifier_parameters is None else classifier_parameters
        self.path_scores = path_scores
        self.path_errors = os.path.join(self.tmp_dir, "errors")
        self.errors_saver = ErrorsSaver(self.path_errors, os.path.join(self.dataset_dir, "dataset.zip"), logger, config=config)
        self.path_features_importances = path_features_importances
        self.label_transformer = identity if label_transformer is None else label_transformer

        if not path_out.endswith(".pkl.gz"):
            path_out = path_out + ".gz" if path_out.endswith(".pkl") else path_out + ".pkl.gz"

        self.path_out = path_out
        self.config = config
        self.n_splits = n_splits

    def fit(self, no_cache: bool = False, cross_val_only: bool = False, save_dataset: bool = False, save_errors_images: bool = False) -> None:
        """
        Fit the line classifier with cross-validation and errors statistics saving.

        :param no_cache: whether to use cached training data (:class:`~scripts.train.trainers.data_loader.DataLoader`)
        :param cross_val_only: whether to execute only cross-validation, without training and saving a resulting classifier
        :param save_dataset: whether to save training dataset in form of a feature matrix (:class:`~scripts.train.trainers.dataset.LineClassifierDataset`)
        :param save_errors_images: whether to visualize errors line classification (:class:`~scripts.train.trainers.errors_saver.ErrorsSaver`)
        """
        data = self.data_loader.get_data(no_cache=no_cache)
        if save_dataset:
            self.__save_dataset_lines(data=data, path=self.tmp_dir)
        scores = self._cross_val(data, save_errors_images)
        logging.info(json.dumps(scores, indent=4))
        if not cross_val_only:
            features = self.feature_extractor.fit_transform(data)
            self.logger.info(f"data train shape {features.shape}")
            n = features.shape[0] // 10
            features_train, features_test = features[:-n], features[-n:]
            labels = self.__get_labels(data)
            labels_train, labels_test = labels[:-n], labels[-n:]

            cls = self._get_classifier()
            sample_weight = [self.get_sample_weight(line) for line in flatten(data)]
            cls.fit(features_train, labels_train, sample_weight=sample_weight[:-n])

            predicted = cls.predict(features_test)
            accuracy = accuracy_score(labels_test, predicted, sample_weight=sample_weight[-n:])
            print(f"Final Accuracy = {accuracy}")
            scores["final_accuracy"] = accuracy

            if not os.path.isdir(os.path.dirname(self.path_out)):
                os.makedirs(os.path.dirname(self.path_out))
            with gzip.open(self.path_out, "wb") as output_file:
                pickle.dump((cls, self.feature_extractor.parameters()), output_file)

            if self.path_scores is not None:
                self.logger.info(f"Save scores in {self.path_scores}")
                os.makedirs(os.path.dirname(self.path_scores), exist_ok=True)
                with open(self.path_scores, "w") as file:
                    json.dump(obj=scores, fp=file, indent=4)
            if self.path_features_importances is not None:
                os.makedirs(os.path.dirname(self.path_features_importances), exist_ok=True)
                self._save_features_importances(cls, features_train.columns)

    def _save_features_importances(self, cls: BaseClassifier, feature_names: List[str]) -> None:
        """
        Save information about most important features for classifier during training into a file with path `self.path_features_importances`.

        :param cls: classifier trained on the features with names `feature_names`
        :param feature_names: column names of the feature matrix, that was used for classifier training
        """
        pass

    def __save_dataset_lines(self, data: List[List[LineWithLabel]], path: str = "/tmp", csv_only: bool = False) -> str:
        """
        Save training dataset in form of a feature matrix (:class:`~scripts.train.trainers.dataset.LineClassifierDataset`).

        :param data: list of documents, which are lists of lines with labels of the training dataset
        :param path: path to the directory where the dataset will be saved
        :param csv_only: whether to save only csv-file instead of saving dataset as a directory with csv, pkl and json files
        :return: path to the directory where the dataset is saved
        """
        features_train = self.feature_extractor.fit_transform(data)
        features_list = sorted(features_train.columns)
        features_train = features_train[features_list]
        label_name = "label"
        features_train[label_name] = self.__get_labels(data)
        group_name = "group"
        features_train[group_name] = [line.group for line in flatten(data)]
        uid_name = "uid"
        features_train[uid_name] = [line.uid for line in flatten(data)]
        text_name = "text"
        features_train[text_name] = [line.line for line in flatten(data)]
        dataset = LineClassifierDataset(dataframe=features_train, feature_list=features_list, group_name=group_name, label_name=label_name, text_name=text_name)
        path = dataset.save(path, csv_only=csv_only)
        self.logger.info(f"Save dataset into {path}")
        return path

    @abc.abstractmethod
    def _get_classifier(self) -> BaseClassifier:
        """
        Initialize the classifier.

        :return: classifier instance for training
        """
        pass

    def _cross_val(self, data: List[List[LineWithLabel]], save_errors_images: bool) -> dict:
        """
        Cross-validate the classifier and save its errors on validation data

        :param data: list of documents, which are lists of lines with labels of the training dataset
        :param save_errors_images: whether to visualize errors line classification (:class:`~scripts.train.trainers.errors_saver.ErrorsSaver`)
        :return: dictionary with classifier scores during cross-validation
        """
        error_cnt = Counter()
        errors_uids = []
        os.system(f"rm -rf {self.path_errors}/*")
        os.makedirs(self.path_errors, exist_ok=True)
        scores = []

        data = np.array(data, dtype=object)
        kf = KFold(n_splits=self.n_splits)

        for train_index, val_index in tqdm(kf.split(data), total=self.n_splits):
            data_train, data_val = data[train_index].tolist(), data[val_index].tolist()
            labels_train = self.__get_labels(data_train)
            labels_val = self.__get_labels(data_val)
            features_train = self.feature_extractor.fit_transform(data_train)
            features_val = self.feature_extractor.transform(data_val)
            if features_train.shape[1] != features_val.shape[1]:
                val_minus_train = set(features_val.columns) - set(features_train.columns)
                train_minus_val = set(features_val.columns) - set(features_train.columns)
                msg = f"Some features in train, but not in val {val_minus_train}\nsome features in val, but not in train {train_minus_val}"
                raise ValueError(msg)
            cls = self._get_classifier()
            sample_weight = [self.get_sample_weight(line) for line in flatten(data_train)]
            cls.fit(features_train, labels_train, sample_weight=sample_weight)
            labels_predict = cls.predict(features_val)

            # save classifier's errors on val set
            for y_pred, y_true, line in zip(labels_predict, labels_val, flatten(data_val)):
                if y_true != y_pred:
                    error_cnt[(y_true, y_pred)] += 1
                    errors_uids.append(line.uid)
                    with open(os.path.join(self.path_errors, f"{y_true}_{y_pred}.txt"), "a") as file:
                        result = OrderedDict()
                        result["text"] = line.line
                        result["uid"] = line.uid
                        result["line_id"] = line.metadata.line_id
                        result["document"] = line.group
                        file.write(json.dumps(result, ensure_ascii=False) + "\n")
            scores.append(accuracy_score(labels_val, labels_predict))

        scores_dict = OrderedDict()
        scores_dict["mean"] = mean(scores)
        scores_dict["scores"] = scores
        csv_path = self.__save_dataset_lines(data=data.tolist(), path=self.dataset_dir, csv_only=True)
        self.errors_saver.save_errors(error_cnt=error_cnt, errors_uids=list(set(errors_uids)), save_errors_images=save_errors_images, csv_path=csv_path)
        return scores_dict

    def __get_labels(self, data: List[List[LineWithLabel]]) -> List[str]:
        """
        :param data: list of documents, which are lists of lines with labels of the training dataset
        :return: a flattened list of lines' labels
        """
        result = [line.label for line in flatten(data)]
        return result
