import gzip
import logging
import os
import pickle
from typing import List

from xgboost import XGBClassifier

from dedoc.config import get_config
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.paragraph_features import ParagraphFeatureExtractor
from dedoc.utils.parameter_utils import get_param_gpu_available


class ScanParagraphClassifierExtractor(object):
    """
    Classifier detects current line is continues
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.logger = config.get("logger", logging.getLogger())
        self.path = os.path.join(get_config()["resources_path"], "paragraph_classifier.pkl.gz")
        self.config = config
        self._feature_extractor = None
        self._classifier = None

    @property
    def feature_extractor(self) -> ParagraphFeatureExtractor:
        if self._feature_extractor is None:
            self._unpickle()
        return self._feature_extractor

    @property
    def classifier(self) -> XGBClassifier:
        if self._classifier is None:
            self._unpickle()
        return self._classifier

    def _unpickle(self) -> None:
        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="paragraph_classifier", hub_name="model.pkl.gz")

        with gzip.open(self.path) as file:
            self._classifier, parameters = pickle.load(file)
            self._feature_extractor = ParagraphFeatureExtractor(**parameters, config=self.config)

        if get_param_gpu_available(self.config, self.logger):
            gpu_params = dict(predictor="gpu_predictor", tree_method="auto", gpu_id=0)
            self._classifier.set_params(**gpu_params)
            self._classifier.get_booster().set_param(gpu_params)

        return self._classifier

    def extract(self, lines_with_links: List[LineWithLocation]) -> List[LineWithLocation]:
        data = self.feature_extractor.transform([lines_with_links])
        if any((data[col].isna().all() for col in data.columns)):
            labels = ["not_paragraph"] * len(lines_with_links)
        else:
            labels = self.classifier.predict(data)
        for label, line in zip(labels, lines_with_links):
            if line.line.strip() == "":
                label = "not_paragraph"
            line.metadata.tag_hierarchy_level.can_be_multiline = label != "paragraph"
        return lines_with_links
