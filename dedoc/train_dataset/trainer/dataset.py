import json
import os
import time
from typing import List

import pandas as pd


class LineClassifierDataset:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 feature_list: List[str],
                 group_name: str,
                 label_name: str,
                 text_name: str) -> None:
        """

        @param dataframe: pandas dataframe with features and metadata
        @param feature_list: list of feature columns name
        @param group_name: name of group column (for example "document")
        @param label_name: name of label column (for example "label")
        """
        super().__init__()
        self.label_name = label_name
        self.group_name = group_name
        self.feature_list = feature_list
        self.text_name = text_name
        self.dataframe = dataframe

    @property
    def features(self) -> pd.DataFrame:
        return self.dataframe[self.feature_list]

    @property
    def labels(self) -> pd.Series:
        return self.dataframe[self.label_name]

    def save(self, path: str = "/tmp", csv_only: bool = False) -> str:
        if csv_only:
            self.dataframe.to_csv(os.path.join(path, "dataset.csv"))
            return path
        dir_out = os.path.join(path, "dataset_{}".format(int(time.time() * 1000)))
        os.mkdir(dir_out)
        self.dataframe.to_csv(os.path.join(dir_out, "dataset.csv"))
        self.dataframe.to_pickle(os.path.join(dir_out, "dataset.pkl.gz"))
        with open(os.path.join(dir_out, "description.json"), "w") as out:
            d = dict(
                label_name=self.label_name,
                group_name=self.group_name,
                text_name=self.text_name,
                feature_list=self.feature_list)
            json.dump(obj=d, fp=out, ensure_ascii=False, indent=4)
        return dir_out
