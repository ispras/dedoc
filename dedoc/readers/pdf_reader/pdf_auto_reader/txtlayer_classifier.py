import gzip
import logging
import os
import pickle
from typing import List

from xgboost import XGBClassifier

from dedoc.config import get_config
from dedoc.data_structures import LineWithMeta
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_feature_extractor import TxtlayerFeatureExtractor
from dedoc.utils.parameter_utils import get_param_gpu_available


class TxtlayerClassifier:
    """
    The TxtlayerClassifier class is used for classifying the correctness of the textual layer in a PDF document.
    """
    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

        self.feature_extractor = TxtlayerFeatureExtractor()
        self.path = os.path.join(get_config()["resources_path"], "txtlayer_classifier.pkl.gz")
        self.__model = None

    @property
    def __get_model(self) -> XGBClassifier:
        if self.__model is not None:
            return self.__model

        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="txtlayer_classifier", hub_name="model.pkl.gz")

        assert os.path.isfile(self.path)
        with gzip.open(self.path, "rb") as f:
            self.__model = pickle.load(f)

        if get_param_gpu_available(self.config, self.logger):
            gpu_params = dict(predictor="gpu_predictor", tree_method="auto", gpu_id=0)
            self.__model.set_params(**gpu_params)
            self.__model.get_booster().set_param(gpu_params)

        return self.__model

    def predict(self, lines: List[LineWithMeta]) -> bool:
        """
        Classifies the correctness of the text layer in a PDF document.

        :param lines: list of document textual lines.
        :returns: True if the textual layer is correct, False otherwise.
        """
        text_layer = "".join([line.line for line in lines])
        if not text_layer:
            return False

        if len(text_layer) < 150:
            text_layer = f"\n{text_layer}" * (150 // len(text_layer))

        features = self.feature_extractor.transform([text_layer])
        return self.__get_model.predict(features)[0] == 1
