import logging
from typing import Optional, Callable
from sklearn.linear_model import LogisticRegression

from dedoc.structure_extractors.feature_extractors.abstract_extractor import AbstractFeatureExtractor
from dedoc.train_dataset.data_structures.line_with_label import LineWithLabel
from dedoc.train_dataset.trainer.base_sklearn_line_classifier import BaseSklearnLineClassifierTrainer


class LogRegLineClassifierTrainer(BaseSklearnLineClassifierTrainer):

    def __init__(self,
                 data_url: str,
                 logger: logging.Logger,
                 feature_extractor: AbstractFeatureExtractor,
                 path_out: str,
                 path_scores: Optional[str] = None,
                 path_features_importances: Optional[str] = None,
                 tmp_dir: Optional[str] = None,
                 train_size: float = 0.75,
                 classifier_parameters: dict = None,
                 label_transformer: Callable[[str], str] = None,
                 random_seed: int = 42,
                 get_sample_weight: Callable[[LineWithLabel], float] = None,
                 n_splits: int = 10,
                 *, config: dict) -> None:

        super().__init__(data_url, logger, feature_extractor, path_out, path_scores, path_features_importances, tmp_dir,
                         train_size, classifier_parameters, label_transformer, random_seed, get_sample_weight, n_splits,
                         config=config)

    def _get_classifier(self) -> LogisticRegression:
        return LogisticRegression(solver="lbfgs", multi_class="auto", max_iter=2000, n_jobs=4)
