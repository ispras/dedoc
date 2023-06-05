import os
from pathlib import Path
from typing import List

import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import f1_score
import gzip
import pickle

from dedoc.readers.pdf_reader.pdf_auto_reader.catboost_model_extractor import CatboostModelExtractor


class GetTextAndTarget:
    """
    The GetTextAndTarget class is used for loading and processing text data from correct and incorrect text files.
    """
    def __init__(self, path_correct_texts: str, path_incorrect_texts: str) -> None:
        self.path_correct_texts = self.make_path(Path(path_correct_texts))
        self.path_incorrect_texts = self.make_path(Path(path_incorrect_texts))
        self.path_all = self.path_correct_texts + self.path_incorrect_texts

    def make_path(self, path: Path) -> List[str]:
        path_all = []
        if path.is_dir():
            for subdir in path.iterdir():
                for subsubdir in subdir.iterdir():
                    path_all.append(str(subsubdir))
        else:
            print("Empty dir ", path)
        return path_all

    def __len__(self) -> int:
        return len(self.path_all)

    def __getitem__(self, item: int) -> dict:
        try:
            with open(self.path_all[item], mode="r") as f:
                text = f.read()
        except Exception as e:
            print(f'Bad file {str(e)}: ', self.path_all[item])

        try:
            if len(text.strip()) == 0:
                raise Exception('Empty file')
        except Exception as error:
            print('Caught this error: ' + str(error))

        label = 1 if self.path_all[item] in str(self.path_correct_texts) else 0

        return {"text": text, "label": label}


class GetFeaturesFromText(CatboostModelExtractor):
    """
    The GetFeaturesFromText class is used for extracting features from text data.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def __len__(self) -> int:
        return len(self.list_symbols)

    def get_feature(self, correct_data_path: str, not_correct_data_path: str) -> dict:
        """
        Generate features and labels for the given dataset.
        :param correct_data_path: Path to the directory containing correct text files.
        :param not_correct_data_path: Path to the directory containing incorrect text files.
        :returns: a dictionary containing features and labels.
        """
        dataset = GetTextAndTarget(path_correct_texts=correct_data_path, path_incorrect_texts=not_correct_data_path)
        label = []
        features = []
        for data in dataset:
            list_of_sub = []
            num_letters_in_data = self._count_letters(data["text"])
            num_other_symboll_in_data = self._count_other(data["text"])
            for symbol in self.list_letters:
                if num_letters_in_data != 0:
                    list_of_sub.append(round(data["text"].count(symbol) / num_letters_in_data, 5))
                else:
                    list_of_sub.append(0.0)
            for symbol in self.list_symbols:
                list_of_sub.append(data["text"].count(symbol))
            list_of_sub.append(num_letters_in_data + num_other_symboll_in_data / len(data["text"]) if len(data["text"]) != 0 else 0)
            features.append(list_of_sub)
            label.append(data["label"])
        return {"features": features, "label": label}

    def get_need_dataframe(self, correct_data_path: str, not_correct_data_path: str, csv_name: str) -> pd.DataFrame:
        """
        Create a DataFrame from the given dataset and save it as a CSV file.
        :param correct_data_path: Path to the directory containing correct text files.
        :param not_correct_data_path: Path to the directory containing incorrect text files.
        :param csv_name: Name of the output CSV file.
        :returns: The generated DataFrame.
        """
        features = self.get_feature(correct_data_path=correct_data_path, not_correct_data_path=not_correct_data_path)
        df = pd.DataFrame(features["features"])
        df.to_csv(csv_name, sep='\t', index=False)
        return df


def train() -> None:
    boost = GetFeaturesFromText(config={})
    features_train = boost.get_feature(correct_data_path=os.getcwd() + "/data/correct/",
                                       not_correct_data_path=os.getcwd() + "/data/not_correct/")
    features_test = boost.get_feature(correct_data_path=os.getcwd() + "/data/correct_test/",
                                      not_correct_data_path=os.getcwd() + "/data/not_correct_test/")
    features_val = boost.get_feature(correct_data_path=os.getcwd() + "/data/correct_val/",
                                     not_correct_data_path=os.getcwd() + "/data/not_correct_val/")

    df_train = pd.DataFrame(features_train["features"])
    df_test = pd.DataFrame(features_test["features"])
    df_val = pd.DataFrame(features_val["features"])
    df_train_label = features_train["label"]
    df_test_label = features_test["label"]
    df_val_label = features_val["label"]

    booster = CatBoostClassifier(iterations=100, verbose=10, task_type="CPU", devices="0")

    train_data = Pool(df_train, df_train_label)
    test_data = Pool(df_test, df_test_label)
    val_data = Pool(df_val, df_val_label)

    booster.fit(train_data, eval_set=val_data, plot=True)

    test_preds = booster.predict(test_data)

    f1_score(df_test_label, test_preds)

    with gzip.open('catboost_detect_tl_correctness.pkl.gz', 'wb') as file:
        pickle.dump(booster, file)
