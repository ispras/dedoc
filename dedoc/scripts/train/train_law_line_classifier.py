import logging
import os
from typing import Optional

from config import _config as config
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from doc_reader.train_dataset.data_structures.line_with_label import LineWithLabel
from doc_reader.train_dataset.trainer.xgboost_line_classifier_trainer import XGBoostLineClassifierTrainer


def transform_labels(label: str) -> Optional[str]:
    label2label = {
        "title": "header",
        "header": "header",
        "article": "structure_unit",
        "item": "structure_unit",
        "subitem": "structure_unit",
        "struct_unit": "structure_unit",
        "part": "structure_unit",
        "structure_unit": "structure_unit",
        "footer": "footer",
        "raw_text": "raw_text",
        "application": "application",
        "Other": None,
        "cellar": "cellar",
        "": None
    }
    return label2label[label]


txt_classifier = True
resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "..", "resources"))
assert os.path.isdir(resources_path)
classifier_name = "law_txt_classifier" if txt_classifier else "law_classifier"
path_out = os.path.join(resources_path, "{}.pkl.gz".format(classifier_name))
path_scores = os.path.join(resources_path, "benchmarks", "{}_scores.json".format(classifier_name))
path_feature_importances = os.path.join(resources_path,
                                        "feature_importances",
                                        "{}_feature_importances.xlsx".format(classifier_name))

feature_extractor = LawTextFeatures(text_features_only=txt_classifier)
classifier_parameters = dict(learning_rate=0.8,
                             n_estimators=300,
                             booster="gbtree",
                             tree_method="hist",
                             max_depth=5,
                             n_jobs=8)


def get_sample_weight(line: LineWithLabel) -> int:
    label = transform_labels(line.label)
    class_weight = {"structure_unit": 5, "header": 0.2, "raw_text": 0.5}.get(label, 1)
    text_with_upper = line.line.strip()
    regexps = LawTextFeatures.named_regexp + [LawTextFeatures.roman_regexp]
    application_regexp = LawTextFeatures.regexp_application_begin
    regexp_weight = 50 if any([regexp.match(text_with_upper) for regexp in regexps]) else 1
    application_weight = 3000 if application_regexp.match(text_with_upper.lower()) else 1

    return regexp_weight * class_weight * application_weight


trainer = XGBoostLineClassifierTrainer(
    data_url="https://at.ispras.ru/owncloud/index.php/s/2y5B5vLHSMh9QrJ/download",
    logger=config.get("logger", logging.getLogger()),
    feature_extractor=feature_extractor,
    path_out=path_out,
    path_scores=path_scores,
    path_features_importances=path_feature_importances,
    tmp_dir="/tmp",
    classifier_parameters=classifier_parameters,
    label_transformer=transform_labels,
    random_seed=42,
    config=config,
    get_sample_weight=get_sample_weight
)

trainer.fit(cross_val_only=False, save_errors_images=False)
print("successfully train law classifier")