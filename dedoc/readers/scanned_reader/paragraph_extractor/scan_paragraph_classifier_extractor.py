import gzip
import os
import pickle
from typing import List

from huggingface_hub import hf_hub_download
from xgboost import XGBClassifier

from dedoc.readers.scanned_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.scanned_reader.paragraph_extractor.paragraph_features import ParagraphFeatureExtractor


class ScanParagraphClassifierExtractor(object):
    """
    Classifier detects current line is continues
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__()
        dirname = os.path.dirname(__file__)
        path = os.path.join(dirname, "..", "..", "..", "..", "resources", "paragraph_classifier.pkl.gz")
        self.path = os.path.abspath(path)
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
            self.path = hf_hub_download(repo_id="dedoc/paragraph_classifier", filename="model.pkl.gz")

        with gzip.open(self.path) as file:
            self._classifier, parameters = pickle.load(file)
            self._feature_extractor = ParagraphFeatureExtractor(**parameters, config=self.config)

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
