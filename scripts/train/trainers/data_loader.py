import gzip
import logging
import os
import pickle
import zipfile
from collections import Counter, defaultdict
from tempfile import TemporaryDirectory
from typing import Callable, List, Tuple

import numpy as np
import pandas as pd
import wget
from torch.utils.data import Dataset

from dedoc.utils.utils import flatten
from train_dataset.data_structures.line_with_label import LineWithLabel
from train_dataset.extractors.line_with_meta_extractor import LineWithMetaExtractor


class DataLoader:
    """
    Class for downloading data from the cloud, distributing lines into document groups and sorting them.
    Returns data in form of document lines with their labels.
    """

    def __init__(self, dataset_dir: str, label_transformer: Callable[[str], str], logger: logging.Logger, data_url: str, *, config: dict) -> None:
        """
        :param dataset_dir: path to the directory where to store downloaded dataset
        :param label_transformer: function for mapping initial data labels into the labels for classifier training
        :param logger: logger for logging details of dataset loading
        :param data_url: url to download data from
        :param config: any custom configuration
        """
        self.label_transformer = label_transformer
        self.dataset_dir = dataset_dir
        self.logger = logger
        self.data_url = data_url
        self.config = config

    def get_data(self, no_cache: bool = False) -> List[List[LineWithLabel]]:
        """
        Download data from a cloud at `self.data_url` and sort document lines.

        :param no_cache: whether to use cached data (if dataset is already downloaded) or download it anyway
        :return: list of documents, which are lists of lines with labels of the training dataset
        """
        pkl_path = os.path.join(self.dataset_dir, "dataset.pkl.gz")

        if os.path.isfile(pkl_path) and not no_cache:
            with gzip.open(pkl_path) as input_file:
                result = pickle.load(input_file)
            self.logger.info("Data were loaded from the local disk")
            return self.__sort_data(result)

        os.makedirs(self.dataset_dir, exist_ok=True)
        path_out = os.path.join(self.dataset_dir, "dataset.zip")
        self.logger.info("Start download dataset")
        wget.download(self.data_url, path_out)
        self.logger.info("Finish download dataset")

        # make list of LineWithLabel instead of dictionary of serialized lines
        with TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(path_out, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)
            metadata_extractor = LineWithMetaExtractor(
                path=os.path.join(tmp_dir, "labeled.json"),
                documents_path=os.path.join(tmp_dir, "original_documents"),
                config=self.config
            )
            data = metadata_extractor.create_task()
        grouped = defaultdict(list)

        # postprocess lines' labels and group them according to their document
        uid_set = set()
        for line in data:
            if line.uid in uid_set:
                continue
            uid_set.add(line.uid)
            transformed_label = self.label_transformer(line.label)
            if transformed_label is not None:
                line.label = transformed_label
                grouped[line.group].append(line)
        result = list(grouped.values())

        self.logger.info(Counter([line.label for line in flatten(result)]))
        pickle.dump(result, gzip.open(pkl_path, "wb"))
        return self.__sort_data(result)

    def __sort_data(self, documents: List[List[LineWithLabel]]) -> List[List[LineWithLabel]]:
        for num, doc in enumerate(documents):
            documents[num] = sorted(doc, key=lambda line: (line.metadata.page_id, line.metadata.line_id))
        return documents


class LineEpsDataSet(Dataset):
    def __init__(self, features: pd.DataFrame, labels: List[str], class_dict: dict, eps: int = 3) -> None:
        self.line_features = features
        if self.line_features is not None:
            self.line_features.index = np.arange(0, len(self.line_features))
        self.line_labels = labels
        self.length = len(self.line_labels)
        self.eps = eps
        self.class_dict = class_dict

    def __len__(self) -> int:
        return len(self.line_labels)

    def __getitem__(self, index: int) -> Tuple[List[float], int, int]:
        line_with_eps_features = []

        for line_id in range(index - self.eps, index + self.eps + 1):
            if line_id < 0 or line_id >= self.length:
                line_with_eps_features.append(np.zeros(self.line_features.shape[1]))
            else:
                line_with_eps_features.append(self.line_features.loc[[line_id]].to_numpy()[0])
        return line_with_eps_features, self.class_dict[self.line_labels[index]], len(line_with_eps_features)
