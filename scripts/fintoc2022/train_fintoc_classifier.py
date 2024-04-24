"""
Training script for the FinTOC 2022 Shared task (https://wp.lancs.ac.uk/cfie/fintoc2022/).
The code is a modification of the winner's solution (ISP RAS team).
"""
import argparse
import logging
import os

from scripts.fintoc2022.trainer import FintocTrainer

clf_params = {
    "en_binary": dict(random_state=42, learning_rate=0.25, max_depth=5, n_estimators=400, colsample_bynode=0.8, colsample_bytree=0.5, tree_method="hist"),
    "fr_binary": dict(random_state=42, learning_rate=0.1, max_depth=5, n_estimators=800, colsample_bynode=0.5, colsample_bytree=0.8, tree_method="approx"),
    "sp_binary": dict(random_state=42, learning_rate=0.25, max_depth=4, n_estimators=600, colsample_bynode=0.5, colsample_bytree=0.5, tree_method="approx"),
    "en_target": dict(random_state=42, learning_rate=0.07, max_depth=4, n_estimators=800, colsample_bynode=1, colsample_bytree=1, tree_method="hist"),
    "fr_target": dict(random_state=42, learning_rate=0.4, max_depth=5, n_estimators=800, colsample_bynode=1, colsample_bytree=0.5, tree_method="exact"),
    "sp_target": dict(random_state=42, learning_rate=0.25, max_depth=3, n_estimators=600, colsample_bynode=0.5, colsample_bytree=1, tree_method="hist")
}


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "fintoc2022"))
    os.makedirs(base_dir, exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=["en", "fr", "sp"], help="Language of training data", default="en")
    parser.add_argument("--reader", choices=["tabby", "txt_layer"], help="Type of PDF reader used for lines extraction", default="tabby")
    parser.add_argument("--cross_val", type=bool, help="Whether to do a cross-validation", default=True)
    parser.add_argument("--n_splits", type=int, help="Number of splits for cross-validation", default=3)
    args = parser.parse_args()

    trainer = FintocTrainer(
        data_url="https://at.ispras.ru/owncloud/index.php/s/EZfm71WimN2h7rC/download",
        logger=logging.getLogger(),
        language=args.language,
        reader_name=args.reader,
        n_splits=args.n_splits,
        classifiers_dir_path=os.path.join(base_dir, "classifiers"),
        scores_dir_path=os.path.join(base_dir, "scores"),
        features_importances_dir_path=os.path.join(base_dir, "features_importances"),
        tmp_dir="/tmp/fintoc/",  # path where dataset and predicted jsons will be saved
        binary_classifier_parameters=clf_params[f"{args.language}_binary"],
        target_classifier_parameters=clf_params[f"{args.language}_target"]
    )

    trainer.fit(cross_val=args.cross_val)
