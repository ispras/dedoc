import json
import logging
import numbers
import os
import tempfile
import zipfile
from typing import List

from xgboost import XGBClassifier

from dedoc.config import get_config
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.structure_extractors.feature_extractors.paragraph_feature_extractor import ParagraphFeatureExtractor
from dedoc.utils.parameter_utils import get_param_gpu_available


class ScanParagraphClassifierExtractor(object):
    """
    Classifier detects current line is continues
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__()
        self.logger = config.get("logger", logging.getLogger())
        self.path = os.path.join(get_config()["resources_path"], "paragraph_classifier.zip")
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
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="paragraph_classifier", hub_name="model.zip")

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(self.path) as archive:
                archive.extractall(tmpdir)

            with open(os.path.join(tmpdir, "parameters.json")) as parameters_file:
                parameters = json.load(parameters_file)
            self._classifier = XGBClassifier()
            self._classifier.load_model(os.path.join(tmpdir, "classifier.json"))
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

            if line.line.strip() == "" or label is None:
                label = "not_paragraph"
            elif isinstance(label, numbers.Integral):
                label = self.classifier.classes_[label]

            line.metadata.tag_hierarchy_level.can_be_multiline = label != "paragraph"

        return lines_with_links
