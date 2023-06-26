import logging
import os
from typing import Optional

from dedoc.config import _config as config
from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.train_dataset.data_structures.line_with_label import LineWithLabel
from dedoc.train_dataset.trainer.logreg_line_classifier_trainer import LogRegLineClassifierTrainer


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
        "": None
    }
    return label2label[label]


txt_classifier = True
resources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "..", "resources"))
assert os.path.isdir(resources_path)
classifier_name = "law_txt_classifier" if txt_classifier else "law_classifier"
path_out = os.path.join(resources_path, "{}_nn.pkl.gz".format(classifier_name))
path_feature_importances = os.path.join(resources_path,
                                        "feature_importances",
                                        "{}_feature_importances_nn.xlsx".format(classifier_name))

feature_extractor = LawTextFeatures(text_features_only=txt_classifier)
path_scores = os.path.join(resources_path, "benchmarks", "{}_nn_scores.json".format(classifier_name))
classifier_parameters = dict(learning_rate=0.8,
                             n_estimators=300,
                             booster="gbtree",
                             tree_method="gpu_hist",
                             max_depth=5)


def get_sample_weight(line: LineWithLabel) -> float:
    label = transform_labels(line.label)
    class_weight = {"structure_unit": 5, "header": 0.2, "raw_text": 0.5}.get(label, 1)
    text = line.line.lower().strip()
    regexps = LawTextFeatures.named_regexp
    application_regexp = LawTextFeatures.regexp_application_begin
    regexp_weight = (50
                     if any([regexp.match(text) for regexp in regexps]) or application_regexp.match(text.lower())
                     else 1)
    return regexp_weight * class_weight


classifier_parameters_nn = dict(multi_class="auto")

trainer = LogRegLineClassifierTrainer(
    data_url="https://at.ispras.ru/owncloud/index.php/s/nDxc7wPQzJxoUXY/download",
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
