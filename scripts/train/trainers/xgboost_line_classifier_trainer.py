from typing import List

import xgbfir
from xgboost import XGBClassifier

from scripts.train.trainers.base_sklearn_line_classifier import BaseSklearnLineClassifierTrainer


class XGBoostLineClassifierTrainer(BaseSklearnLineClassifierTrainer):
    """
    Trainer of XGBoost line classifier.
    See documentation of `XGBClassifier <https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier>`_ to get more details.
    """

    def _get_classifier(self) -> XGBClassifier:
        """
        Initialize the XGBClassifier.

        :return: XGBClassifier instance for training
        """
        return XGBClassifier(random_state=self.random_seed, **self.classifier_parameters)

    def _save_features_importances(self, cls: XGBClassifier, feature_names: List[str]) -> None:
        """
        Save information about most important features for XGBClassifier using `xgbfir <https://github.com/limexp/xgbfir>`_ library.

        :param cls: XGBClassifier trained on the features with names `feature_names`
        :param feature_names: column names of the feature matrix, that was used for classifier training
        """
        xgbfir.saveXgbFI(cls, feature_names=feature_names, OutputXlsxFile=self.path_features_importances)
