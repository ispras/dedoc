import gzip
import json
import os
import pickle
import shutil
from statistics import mean
from typing import List, Optional, Union

import pandas as pd
import xgbfir
import xgboost as xgb
from sklearn.model_selection import GroupKFold
from tqdm import tqdm

from dedoc.structure_extractors.feature_extractors.fintoc_feature_extractor import FintocFeatureExtractor
from train_dataset.data_structures.line_with_label import LineWithLabel


class FintocClassifier:

    def __init__(self,
                 tocs_path: str,
                 save_path: str,
                 binary_classifier_params: Optional[dict] = None,
                 target_classifier_params: Optional[dict] = None,
                 load_trained: bool = False,
                 lang: str = "en"):
        self.save_path = save_path
        self.lang = lang
        if load_trained:
            with gzip.open(os.path.join(self.save_path, f"binary_classifier_{self.lang}.pkg.gz"), "rb") as input_file:
                self.binary_classifier = pickle.load(file=input_file)
            with gzip.open(os.path.join(self.save_path, f"target_classifier_{self.lang}.pkg.gz"), "rb") as input_file:
                self.target_classifier = pickle.load(file=input_file)
        else:
            assert(binary_classifier_params is not None and target_classifier_params is not None)
            self.binary_classifier = xgb.XGBClassifier(**binary_classifier_params)
            self.target_classifier = xgb.XGBClassifier(**target_classifier_params)
        with open(tocs_path) as f:
            tocs = json.load(f)
        self.features_extractor = FintocFeatureExtractor(tocs)

    def fit(self, data: Union[pd.DataFrame, List[LineWithLabel]],
            cross_val: bool = True,
            save: bool = False,
            gt_dir: Optional[str] = None,
            n_splits: int = 3) -> None:
        if isinstance(data, pd.DataFrame):
            features_df = data
        else:
            features_df = lines2dataframe(data, self.features_extractor)
        print("Features shape: {}".format(features_df.shape))
        results = None

        if cross_val:
            assert(gt_dir is not None)
            results = self.evaluate_fintoc_metric(features_df=features_df, gt_dir=gt_dir, n_splits=n_splits)

        if not save:
            return

        features_names = self.__get_features_names(features_df)
        self.binary_classifier.fit(features_df[features_names], features_df.label != -1)
        self.target_classifier.fit(features_df[features_names][features_df.label != -1],
                                   features_df.label[features_df.label != -1])
        self._save(features_names, results)

    def _save(self, features_names: list, scores: Optional[dict]) -> None:
        os.makedirs(self.save_path, exist_ok=True)
        if scores is not None:
            with open(os.path.join(self.save_path, f"scores_{self.lang}.json"), "w") as f:
                json.dump(scores, f)
            print("Scores were saved in {}".format(os.path.join(self.save_path, f"scores_{self.lang}.json")))

        with gzip.open(os.path.join(self.save_path, F"binary_classifier_{self.lang}.pkg.gz"), "wb") as output_file:
            pickle.dump(self.binary_classifier, output_file)
        with gzip.open(os.path.join(self.save_path, f"target_classifier_{self.lang}.pkg.gz"), "wb") as output_file:
            pickle.dump(self.target_classifier, output_file)
        print("Classifiers were saved in {} directory".format(self.save_path))

        xgbfir.saveXgbFI(self.binary_classifier, feature_names=features_names,
                         OutputXlsxFile=os.path.join(self.save_path, f"feature_importances_binary_{self.lang}.xlsx"))
        xgbfir.saveXgbFI(self.target_classifier, feature_names=features_names,
                         OutputXlsxFile=os.path.join(self.save_path, f"feature_importances_target_{self.lang}.xlsx"))
        print("Features importances were saved in {} directory".format(self.save_path))

    def predict(self, data: Union[pd.DataFrame, List[LineWithLabel]]) -> dict:
        """
        param lines: list of documents lines, label isn't known or dataframe with lines features
        :return: dict with TOC of the documents in the required format
        """
        if isinstance(data, pd.DataFrame):
            features_df = data
        else:
            features_df = lines2dataframe(data, self.features_extractor)
        features_names = self.__get_features_names(features_df)
        binary_predictions = self.binary_classifier.predict(features_df[features_names])
        features_df["label"] = binary_predictions
        target_predictions = self.target_classifier.predict(features_df[features_names][features_df.label])
        result_dict = create_json_result(features_df[features_df.label], target_predictions)
        return result_dict

    def evaluate_fintoc_metric(self,
                               features_df: pd.DataFrame,
                               gt_dir: str,
                               n_splits: int = 3) -> dict:

        features_names = self.__get_features_names(features_df)
        results_path = os.path.join(self.save_path, "results")
        os.makedirs(results_path, exist_ok=True)

        kf = GroupKFold(n_splits=n_splits)

        result_scores = {"td_scores": [], "toc_scores": []}
        for i, (train_index, val_index) in tqdm(enumerate(kf.split(features_df, groups=features_df.group)),
                                                total=n_splits):
            df_train = features_df.loc[train_index]
            df_val = features_df.loc[val_index]
            self.binary_classifier.fit(df_train[features_names], df_train.label != -1)
            self.target_classifier.fit(
                df_train[features_names][df_train.label != -1], df_train.label[df_train.label != -1])
            result_dict = self.predict(df_val)

            tmpdir = "/tmp/fintoc/eval"
            if os.path.isdir(tmpdir):
                shutil.rmtree(tmpdir)
            os.makedirs(tmpdir)
            tmp_gt_dir, predictions_dir = os.path.join(tmpdir, "groundtruth"), os.path.join(tmpdir, "predictions")
            os.makedirs(tmp_gt_dir)
            os.makedirs(predictions_dir)

            for doc_name, result in result_dict.items():
                gt_doc_name = doc_name + ".pdf.fintoc4.json"
                if gt_doc_name not in os.listdir(gt_dir):
                    print(f"\n{gt_doc_name} not found in groundtruth")
                    continue
                with open(os.path.join(predictions_dir, gt_doc_name), "w") as json_file:
                    json.dump(result, json_file, indent=2)
                shutil.copy(os.path.join(gt_dir, gt_doc_name), os.path.join(tmp_gt_dir, gt_doc_name))
            score(tmp_gt_dir, predictions_dir)
            shutil.rmtree(tmpdir)

            path_scores = os.path.join(results_path, str(i))
            os.makedirs(path_scores, exist_ok=True)
            for file_name in ['td.log', 'toc.log', 'td_report.csv', 'toc_report.csv']:
                shutil.move(file_name, os.path.join(path_scores, file_name))
            f1, inex_f1 = get_values_from_csv(path_scores)
            result_scores["td_scores"].append(f1)
            result_scores["toc_scores"].append(inex_f1)
            print(f"it {i}:\ntd  {result_scores['td_scores'][-1]}\ntoc {result_scores['toc_scores'][-1]}")
        result_scores["td_mean"] = mean(result_scores["td_scores"])
        result_scores["toc_mean"] = mean(result_scores["toc_scores"])
        return result_scores

    def __get_features_names(self, features_df: pd.DataFrame) -> list:
        features_names = [col for col in features_df.columns if col not in ("text", "label", "group", "uid")]
        return features_names


def train_classifier(train_dir: str) -> None:
    clf_params = {
        "en_binary": dict(random_state=42, learning_rate=0.25, max_depth=5, n_estimators=400,
                          colsample_bynode=0.8, colsample_bytree=0.5, tree_method="hist"),
        "fr_binary": dict(random_state=42, learning_rate=0.1, max_depth=5, n_estimators=800,
                          colsample_bynode=0.5, colsample_bytree=0.8, tree_method="approx"),
        "sp_binary": dict(random_state=42, learning_rate=0.25, max_depth=4, n_estimators=600,
                          colsample_bynode=0.5, colsample_bytree=0.5, tree_method="approx"),
        "en_target": dict(random_state=42, learning_rate=0.07, max_depth=4, n_estimators=800,
                          colsample_bynode=1, colsample_bytree=1, tree_method="hist"),
        "fr_target": dict(random_state=42, learning_rate=0.4, max_depth=5, n_estimators=800,
                          colsample_bynode=1, colsample_bytree=0.5, tree_method="exact"),
        "sp_target": dict(random_state=42, learning_rate=0.25, max_depth=3, n_estimators=600,
                          colsample_bynode=0.5, colsample_bytree=1, tree_method="hist")
    }
    for lang in ("en", "fr", "sp"):
        pandas_path = os.path.join(train_dir, "pandas", f"lines_{lang}_txt_layer_df.csv.gz")
        cls = FintocClassifier(binary_classifier_params=clf_params[f"{lang}_binary"],
                               target_classifier_params=clf_params[f"{lang}_target"],
                               tocs_path=os.path.join(train_dir, "toc", f"{lang}_toc.json"),
                               save_path="resources",
                               load_trained=False,
                               lang=lang)
        features_df = pd.read_csv(pandas_path, index_col=False)
        cls.fit(data=features_df,
                cross_val=True,
                save=True,
                gt_dir=os.path.join(train_dir, "data", lang, "annots"))


def get_results(test_dir: str) -> None:
    for lang in ("en", "fr", "sp"):
        pandas_path = os.path.join(test_dir, "pandas", f"lines_{lang}_txt_layer_df.csv.gz")
        cls = FintocClassifier(tocs_path=os.path.join(test_dir, "toc", f"{lang}_toc.json"),
                               save_path="resources",
                               load_trained=True,
                               lang=lang)
        features_df = pd.read_csv(pandas_path, index_col=False)
        result_dict = cls.predict(features_df)
        results_dir = os.path.join(test_dir, "results", lang)
        os.makedirs(results_dir, exist_ok=True)
        for doc_name, result in result_dict.items():
            json_doc_name = doc_name + ".pdf.fintoc4.json"
            with open(os.path.join(results_dir, json_doc_name), "w") as json_file:
                json.dump(result, json_file, indent=2)


if __name__ == "__main__":
    train = False
    fintoc_dir = "/home/nasty/fintoc2022"
    if train:
        train_classifier(os.path.join(fintoc_dir, "train"))
    else:
        get_results(os.path.join(fintoc_dir, "test"))
