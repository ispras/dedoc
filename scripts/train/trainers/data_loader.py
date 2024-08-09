import gzip
import logging
import os
import pickle
import zipfile
from tempfile import TemporaryDirectory
from typing import Callable, List

import wget

from train_dataset.data_structures.line_with_label import LineWithLabel


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

    def get_data(self, no_cache: bool = False, loading_with_annotation_update: bool = False) -> List[List[LineWithLabel]]:
        """
        Download data from a cloud at `self.data_url` and sort document lines.

        :param no_cache: whether to use cached data (if dataset is already downloaded) or download it anyway
        :param loading_with_annotation_update: True if the dataset is out of date (lines' annotations in dataset are out of date.
            Not recommended method of loading dataset.

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
        if not os.path.isfile(path_out):
            self.logger.info("Start download dataset")
            wget.download(self.data_url, path_out)
            self.logger.info("Finish download dataset")

        # make list of LineWithLabel instead of dictionary of serialized lines
        with TemporaryDirectory() as tmp_dir:
            with zipfile.ZipFile(path_out, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)

            if loading_with_annotation_update:
                from train_dataset.extractors.line_with_label_extractor import LoadAndUpdateGTLineWithLabel
                line_extractor = LoadAndUpdateGTLineWithLabel(labels_path=os.path.join(tmp_dir, "labeled.json"),
                                                              documents_path=os.path.join(tmp_dir, "original_documents"),
                                                              parameters_path=os.path.join(tmp_dir, "parameters.json"),
                                                              logfile_dir=self.dataset_dir)
            else:
                from train_dataset.extractors.line_with_label_extractor import LoadGTLineWithLabel
                line_extractor = LoadGTLineWithLabel(labels_path=os.path.join(tmp_dir, "labeled.json"),
                                                     documents_path=os.path.join(tmp_dir, "original_documents"),
                                                     logfile_dir=self.dataset_dir)

            docs = line_extractor.load_gt()

        docs = self.__postprocess_lines(docs)
        return self.__sort_data(docs)

    def __postprocess_lines(self, docs: List[List[LineWithLabel]]) -> List[List[LineWithLabel]]:
        """ Postprocess line's labels according to user's function `label_transformer`"""
        for doc in docs:
            for line in doc:
                transformed_label = self.label_transformer(line.label)
                if transformed_label is not None:
                    line.label = transformed_label
        return docs

    def __sort_data(self, documents: List[List[LineWithLabel]]) -> List[List[LineWithLabel]]:
        for num, doc in enumerate(documents):
            documents[num] = sorted(doc, key=lambda line: (line.metadata.page_id, line.metadata.line_id))
        return documents
