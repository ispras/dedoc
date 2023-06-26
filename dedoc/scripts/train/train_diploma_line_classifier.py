import logging
import os
from typing import Optional

from dedoc.structure_extractors.feature_extractors.diploma_feature_extractor import DiplomaFeatureExtractor

from dedoc.config import _config as config
from dedoc.train_dataset.trainer.xgboost_line_classifier_trainer import XGBoostLineClassifierTrainer


def skip_labels(label: str) -> Optional[str]:
    if label == "named_item_continue":
        return "named_item"
    if label in ("raw_text", "title", "named_item", "toc"):
        return label
    return None


classifier_name = "diploma_classifier"

clf_resources_path = os.path.join(os.path.expanduser('~'), ".cache", "dedoc", "resources", "line_type_classifiers")
os.makedirs(clf_resources_path, exist_ok=True)
resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources"))
assert os.path.isdir(resources_path)

path_out = os.path.join(clf_resources_path, "{}.pkl.gz".format(classifier_name))
path_scores = os.path.join(resources_path, "benchmarks", "{}_scores.json".format(classifier_name))
path_feature_importances = os.path.join(resources_path,
                                        "feature_importances",
                                        "{}_feature_importances.xlsx".format(classifier_name))

feature_extractor = DiplomaFeatureExtractor()
classifier_parameters = dict(learning_rate=0.5,
                             n_estimators=600,
                             booster="gbtree",
                             tree_method="hist",
                             max_depth=3,
                             colsample_bynode=0.8,
                             colsample_bytree=1)

trainer = XGBoostLineClassifierTrainer(
    data_url="https://at.ispras.ru/owncloud/index.php/s/TNFXFQQKICa5oGy/download",
    logger=config.get("logging", logging.getLogger()),
    feature_extractor=feature_extractor,
    path_out=path_out,
    path_scores=path_scores,
    path_features_importances=path_feature_importances,
    tmp_dir="/tmp",
    label_transformer=skip_labels,
    classifier_parameters=classifier_parameters,
    random_seed=42,
    config=config,
)

trainer.fit(cross_val_only=False, save_errors_images=False, no_cache=False)
print("successfully train diploma classifier")
