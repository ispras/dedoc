import os
import zipfile
from pathlib import Path
from typing import List, Tuple

import wget
import xgbfir
from sklearn.metrics import f1_score
from xgboost import XGBClassifier

from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_feature_extractor import TxtlayerFeatureExtractor


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
                if str(file_path).endswith(".txt"):
                    path_all.append(str(file_path))

        return path_all

    def get_texts_and_targets(self) -> Tuple[List[str], List[int]]:
        texts, labels = [], []

        for path in self.path_all:
            try:
                with open(path, mode="r") as f:
                    text = f.read()
            except Exception as e:
                print(f"Bad file {str(e)}: {path}")
                continue

            if len(text.strip()) == 0:
                print(f"Empty file: {path}")
                continue

            texts.append(text)
            labels.append(int(path in str(self.path_correct_texts)))

        return texts, labels


if __name__ == "__main__":
    data_dir = os.path.join(get_config()["intermediate_data_path"], "text_layer_correctness_data")
    os.makedirs(data_dir, exist_ok=True)
    txtlayer_classifier_dataset_dir = os.path.join(data_dir, "data")

    if not os.path.isdir(txtlayer_classifier_dataset_dir):
        path_out = os.path.join(data_dir, "data.zip")
        wget.download("https://at.ispras.ru/owncloud/index.php/s/z9WLFiKKFo2WMgW/download", path_out)
        with zipfile.ZipFile(path_out, "r") as zip_ref:
            zip_ref.extractall(data_dir)
        os.remove(path_out)
        print(f"Dataset downloaded to {txtlayer_classifier_dataset_dir}")
    else:
        print(f"Use cached dataset from {txtlayer_classifier_dataset_dir}")

    assert os.path.isdir(txtlayer_classifier_dataset_dir)

    features_extractor = TxtlayerFeatureExtractor()
    stages_data = {}

    for stage in ["train", "test", "val"]:
        texts, labels = GetTextAndTarget(os.path.join(txtlayer_classifier_dataset_dir, f"correct_{stage}"),
                                         os.path.join(txtlayer_classifier_dataset_dir, f"not_correct_{stage}")).get_texts_and_targets()
        features = features_extractor.transform(texts)
        stages_data[stage] = dict(features=features, labels=labels)

    clf = XGBClassifier(random_state=42, learning_rate=0.5, n_estimators=600, booster="gbtree", tree_method="hist", max_depth=3)
    clf.fit(X=stages_data["train"]["features"], y=stages_data["train"]["labels"], eval_set=[(stages_data["val"]["features"], stages_data["val"]["labels"])])
    test_preds = clf.predict(stages_data["test"]["features"])

    score = f1_score(stages_data["test"]["labels"], test_preds)
    print(f"F1 score = {score}")

    resources_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "resources")
    clf.save_model(os.path.join(resources_dir, "txtlayer_classifier.json"))

    xgbfir.saveXgbFI(clf,
                     feature_names=features.columns,
                     OutputXlsxFile=os.path.join(resources_dir, "feature_importances", "txtlayer_classifier_feature_importances.xlsx"))
