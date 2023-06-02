import abc
import gzip
import hashlib
import json
import logging
import os
import pickle
from collections import Counter, OrderedDict
from statistics import mean
from typing import Optional, List, Callable, Any
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold
from tqdm import tqdm
from xgboost import XGBClassifier

from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.train_dataset.data_structures.line_with_label import LineWithLabel
from dedoc.train_dataset.trainer.data_loader import DataLoader
from dedoc.train_dataset.trainer.dataset import LineClassifierDataset
from dedoc.train_dataset.trainer.errors_saver import ErrorsSaver
from dedoc.utils.utils import flatten, identity


class BaseClassifier(XGBClassifier):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class BaseSklearnLineClassifierTrainer:

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

        self.data_url = data_url
        self.logger = logger
        self.feature_extractor = feature_extractor
        self.tmp_dir = "/tmp" if tmp_dir is None else tmp_dir
        url_hash = hashlib.md5(self.data_url.encode()).hexdigest()
        self.dataset_dir = os.path.join(self.tmp_dir, "dataset_{}".format(url_hash))
        self.data_loader = DataLoader(dataset_dir=self.dataset_dir,
                                      label_transformer=label_transformer,
                                      logger=logger,
                                      data_url=data_url,
                                      config=config)
        self.random_seed = random_seed
        self.get_sample_weight = get_sample_weight if get_sample_weight is not None else lambda t: 1
        os.makedirs(self.tmp_dir, exist_ok=True)
        assert train_size > 0
        assert train_size < 1 or 1 < train_size < 100
        self.train_size = train_size if train_size < 1 else train_size / 100
        self.classifier_parameters = {} if classifier_parameters is None else classifier_parameters
        self.path_scores = path_scores
        self.path_errors = os.path.join(self.tmp_dir, "errors")
        self.errors_saver = ErrorsSaver(self.path_errors, self.dataset_dir, logger, config=config)
        self.path_features_importances = path_features_importances
        self.label_transformer = identity if label_transformer is None else label_transformer

        if path_out.endswith(".pkl"):
            path_out += ".gz"
        elif path_out.endswith("pkl.gz"):
            pass
        else:
            path_out += ".pkl.gz"
        self.path_out = path_out
        self.config = config
        self.n_splits = n_splits

    def fit(self, no_cache: bool = False,
            cross_val_only: bool = False,
            save: bool = False,
            save_errors_images: bool = False) -> None:
        data = self.data_loader.get_data(no_cache=no_cache)
        if save:
            self.__save(data=data, path=self.tmp_dir)
        scores = self._cross_val(data, save_errors_images)
        logging.info(json.dumps(scores, indent=4))
        if not cross_val_only:
            features = self.feature_extractor.fit_transform(data)
            self.logger.info("data train shape {}".format(features.shape))
            n = features.shape[0] // 10
            features_train, features_test = features[:-n], features[-n:]
            labels = self.__get_labels(data)
            labels_train, labels_test = labels[:-n], labels[-n:]

            cls = self._get_classifier()
            sample_weight = [self.get_sample_weight(line) for line in flatten(data)]
            cls.fit(features_train, labels_train, sample_weight=sample_weight[:-n])

            predicted = cls.predict(features_test)
            accuracy = accuracy_score(labels_test, predicted, sample_weight=sample_weight[-n:])
            print("Final Accuracy = {}".format(accuracy))  # noqa
            scores["final_accuracy"] = accuracy

            if not os.path.isdir(os.path.dirname(self.path_out)):
                os.makedirs(os.path.dirname(self.path_out))
            with gzip.open(self.path_out, "wb") as output_file:
                pickle.dump((cls, self.feature_extractor.parameters()), output_file)

            if self.path_scores is not None:
                self.logger.info("Save scores in {}".format(self.path_scores))
                os.makedirs(os.path.dirname(self.path_scores), exist_ok=True)
                with open(self.path_scores, "w") as file:
                    json.dump(obj=scores, fp=file, indent=4)
            if self.path_features_importances is not None:
                os.makedirs(os.path.dirname(self.path_features_importances), exist_ok=True)
                self._save_features_importances(cls, features_train.columns)

    def _save_features_importances(self, cls: Any, feature_names: List[str]) -> None:
        pass

    def __save(self, data: List[List[LineWithLabel]], path: str = "/tmp", csv_only: bool = False) -> str:
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
        dataset = LineClassifierDataset(dataframe=features_train,
                                        feature_list=features_list,
                                        group_name=group_name,
                                        label_name=label_name,
                                        text_name=text_name)
        path = dataset.save(path, csv_only=csv_only)
        self.logger.info("Save dataset into {}".format(path))
        return path

    @abc.abstractmethod
    def _get_classifier(self) -> BaseClassifier:
        pass

    def _cross_val(self, data: List[List[LineWithLabel]], save_errors_images: bool) -> dict:
        error_cnt = Counter()
        errors_uids = []
        os.system("rm -rf {}/*".format(self.path_errors))
        os.makedirs(self.path_errors, exist_ok=True)
        scores = []

        data = np.array(data, dtype=object)
        kf = KFold(n_splits=self.n_splits)
        for iteration, (train_index, val_index) in tqdm(enumerate(kf.split(data)), total=self.n_splits):
            data_train, data_val = data[train_index].tolist(), data[val_index].tolist()
            labels_train = self.__get_labels(data_train)
            labels_val = self.__get_labels(data_val)
            features_train = self.feature_extractor.fit_transform(data_train)
            features_val = self.feature_extractor.transform(data_val)
            if features_train.shape[1] != features_val.shape[1]:
                val_minus_train = set(features_val.columns) - set(features_train.columns)
                train_minus_val = set(features_val.columns) - set(features_train.columns)
                msg = "some features in train, but not in val {}\nsome features in val, but not in train {}".format(
                    val_minus_train, train_minus_val)
                raise ValueError(msg)
            cls = self._get_classifier()
            sample_weight = [self.get_sample_weight(line) for line in flatten(data_train)]
            cls.fit(features_train, labels_train, sample_weight=sample_weight)
            labels_predict = cls.predict(features_val)
            for y_pred, y_true, line in zip(labels_predict, labels_val, flatten(data_val)):
                if y_true != y_pred:
                    error_cnt[(y_true, y_pred)] += 1
                    errors_uids.append(line.uid)
                    with open(os.path.join(self.path_errors, "{}_{}.txt".format(y_true, y_pred)), "a") as file:
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
        csv_path = self.__save(data=data.tolist(), path=self.dataset_dir, csv_only=True)
        self.errors_saver.save_errors(error_cnt=error_cnt, errors_uids=list(set(errors_uids)),
                                      save_errors_images=save_errors_images, csv_path=csv_path)
        return scores_dict

    def __get_labels(self, data: List[List[LineWithLabel]]) -> List[str]:
        result = [line.label for line in flatten(data)]
        return result
