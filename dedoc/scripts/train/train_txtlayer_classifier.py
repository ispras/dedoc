import gzip
import os
import pickle
from pathlib import Path
from typing import List, Tuple

import xgbfir
from sklearn.metrics import f1_score
from xgboost import XGBClassifier

from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier import TxtlayerFeatureExtractor


class GetTextAndTarget:
    """
    The GetTextAndTarget class is used for loading and processing text data from correct and incorrect text files.
    """
    def __init__(self, path_correct_texts: str, path_incorrect_texts: str) -> None:
        self.path_correct_texts = self.__make_path(Path(path_correct_texts))
        self.path_incorrect_texts = self.__make_path(Path(path_incorrect_texts))
        self.path_all = self.path_correct_texts + self.path_incorrect_texts

    def __make_path(self, path: Path) -> List[str]:
        if not path.is_dir():
            return []

        path_all = []
        for subdir in path.iterdir():
            if not subdir.is_dir():
                continue
            for file_path in subdir.iterdir():
                if str(file_path).endswith("txt"):
                    path_all.append(str(file_path))

        return path_all

    def get_texts_and_targets(self) -> Tuple[List[str], List[int]]:
        texts, labels = [], []

        for path in self.path_all:
            try:
                with open(path, mode="r") as f:
                    text = f.read()
            except Exception as e:
                print(f'Bad file {str(e)}: {path}')
                continue

            if len(text.strip()) == 0:
                print(f'Empty file: {path}')
                continue

            texts.append(text)
            labels.append(int(path in str(self.path_correct_texts)))

        return texts, labels


if __name__ == "__main__":
    features_extractor = TxtlayerFeatureExtractor()
    stages_data = {}

    for stage in ["train", "test", "val"]:
        texts, labels = GetTextAndTarget(path_correct_texts=os.getcwd() + f"/data/correct_{stage}/",
                                         path_incorrect_texts=os.getcwd() + f"/data/not_correct_{stage}/").get_texts_and_targets()
        features = features_extractor.transform(texts)
        stages_data[stage] = dict(features=features, labels=labels)

    clf = XGBClassifier(random_state=42, learning_rate=0.5, n_estimators=600, booster="gbtree", tree_method="hist", max_depth=3)
    clf.fit(
        X=stages_data["train"]["features"],
        y=stages_data["train"]["labels"],
        eval_set=[(stages_data["val"]["features"], stages_data["val"]["labels"])],
    )
    test_preds = clf.predict(stages_data["test"]["features"])

    score = f1_score(stages_data["test"]["labels"], test_preds)
    print(f"F1 score = {score}")

    resources_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "..", "resources")
    with gzip.open(os.path.join(resources_dir, 'txtlayer_classifier.pkl.gz'), 'wb') as file:
        pickle.dump(clf, file)

    xgbfir.saveXgbFI(clf,
                     feature_names=features.columns,
                     OutputXlsxFile=os.path.join(resources_dir, "feature_importances", 'txtlayer_classifier_feature_importances.xlsx'))
