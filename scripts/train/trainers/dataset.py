import json
import os
import time
from typing import List

import pandas as pd


class LineClassifierDataset:
    """
    Dataset of lines in form of a feature matrix (with already extracted features)
    """

    def __init__(self, dataframe: pd.DataFrame, feature_list: List[str], group_name: str, label_name: str, text_name: str) -> None:
        """
        :param dataframe: pandas dataframe with features and metadata, columns are features (and metadata), rows are documents' lines
        :param feature_list: list of feature columns' names
        :param group_name: name of the group column, e.g., "document" (dataset is split into groups, one group of lines is related to one document)
        :param label_name: name of the label column, e.g., "label"
        :param text_name: name of the column with lines' text, e.g., "text"
        """
        self.label_name = label_name
        self.group_name = group_name
        self.feature_list = feature_list
        self.text_name = text_name
        self.dataframe = dataframe

    @property
    def features(self) -> pd.DataFrame:
        """
        pandas dataframe with features, columns are features, rows are documents' lines
        """
        return self.dataframe[self.feature_list]

    @property
    def labels(self) -> pd.Series:
        """
        a vector of labels for each line
        """
        return self.dataframe[self.label_name]

    def save(self, path: str = "/tmp", csv_only: bool = False) -> str:
        """
        :param path: path to the directory where the dataset will be saved
        :param csv_only: whether to save only csv-file instead of saving dataset as a directory with csv, pkl and json files
        :return: path to the directory where the dataset is saved
        """
        if csv_only:
            self.dataframe.to_csv(os.path.join(path, "dataset.csv"))
            return path

        dir_out = os.path.join(path, f"dataset_{int(time.time() * 1000)}")
        os.mkdir(dir_out)
        self.dataframe.to_csv(os.path.join(dir_out, "dataset.csv"))
        self.dataframe.to_pickle(os.path.join(dir_out, "dataset.pkl.gz"))

        with open(os.path.join(dir_out, "description.json"), "w") as out:
            d = dict(label_name=self.label_name, group_name=self.group_name, text_name=self.text_name, feature_list=self.feature_list)
            json.dump(obj=d, fp=out, ensure_ascii=False, indent=4)
        return dir_out
