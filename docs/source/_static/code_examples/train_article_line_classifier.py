import logging
import os
from typing import Optional

from article_feature_extractor import ArticleFeatureExtractor

from dedoc.config import get_config
from scripts.train.trainers.xgboost_line_classifier_trainer import XGBoostLineClassifierTrainer


def skip_labels(label: str) -> Optional[str]:
    """
    Function for filtering `other` lines and do not train the classifier on them
    """
    if label == "other":
        return None
    return label


classifier_name = "article_classifier"

# configure path for saving a trained classifier
classifier_directory_path = os.path.join(os.path.expanduser("~"), ".cache", "dedoc", "resources", "line_type_classifiers")
os.makedirs(classifier_directory_path, exist_ok=True)
classifier_path = os.path.join(classifier_directory_path, f"{classifier_name}.zip")

# configure paths for saving scores and features importances (this is not obligatory)
resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources"))
assert os.path.isdir(resources_path)
path_scores = os.path.join(resources_path, "benchmarks", f"{classifier_name}_scores.json")
path_feature_importances = os.path.join(resources_path, "feature_importances", f"{classifier_name}_feature_importances.xlsx")

# features extractor for the classifier
feature_extractor = ArticleFeatureExtractor()

# parameters of the XGBClassifier (https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier)
classifier_parameters = dict(learning_rate=0.5, n_estimators=600, booster="gbtree", tree_method="hist", max_depth=3, colsample_bynode=0.8)

# dedoc configuration (just in case)
config = get_config()

# trainer initialization
trainer = XGBoostLineClassifierTrainer(
    data_url="url with training dataset",
    logger=config.get("logging", logging.getLogger()),
    feature_extractor=feature_extractor,
    path_out=classifier_path,
    path_scores=path_scores,
    path_features_importances=path_feature_importances,
    tmp_dir="/tmp",
    label_transformer=skip_labels,
    classifier_parameters=classifier_parameters,
    random_seed=42,
    config=config,
)

# run training of the classifier
trainer.fit(cross_val_only=False, save_errors_images=False, no_cache=False)
