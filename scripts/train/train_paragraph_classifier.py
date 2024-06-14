import logging
import os
from typing import Optional

from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.paragraph_features import ParagraphFeatureExtractor
from scripts.train.trainers.xgboost_line_classifier_trainer import XGBoostLineClassifierTrainer


def skip_labels(label: str) -> Optional[str]:
    if label not in ("other", "footer", "Other"):
        return label
    return None


classifier_name = "paragraph_classifier"

resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources"))
assert os.path.isdir(resources_path)
path_out = os.path.join(resources_path, f"{classifier_name}.pkl.gz")
path_scores = os.path.join(resources_path, "benchmarks", f"{classifier_name}_scores.json")
path_feature_importances = os.path.join(resources_path, "feature_importances", f"{classifier_name}_feature_importances.xlsx")

config = get_config()
feature_extractor = ParagraphFeatureExtractor(config=config)

classifier_parameters = dict(learning_rate=0.6,
                             n_estimators=350,
                             booster="gbtree",
                             max_depth=6,
                             colsample_bynode=0.1,
                             colsample_bytree=1)


trainer = XGBoostLineClassifierTrainer(
    data_url="https://at.ispras.ru/owncloud/index.php/s/gLvUSYvsCjvKtGg/download",
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

trainer.fit(cross_val_only=False, save_errors_images=False)
print(f"successfully train {classifier_name} classifier")
