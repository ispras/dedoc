import os
from typing import List

import numpy as np
from xgboost import XGBClassifier

from dedoc.config import get_config
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.txtlayer_feature_extractor import TxtlayerFeatureExtractor
from dedoc.utils.parameter_utils import get_param_gpu_available


class MlTxtlayerClassifier(AbstractTxtlayerClassifier):
    """
    The MlTxtlayerClassifier class is used for classifying the correctness of the textual layer in a PDF document
    using XGBClassifier (only for languages based on cyrillic- or latin-based alphabets).
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.feature_extractor = TxtlayerFeatureExtractor()
        self.path = os.path.join(get_config()["resources_path"], "txtlayer_classifier.json")
        self.__model = None

    @property
    def __get_model(self) -> XGBClassifier:
        if self.__model is not None:
            return self.__model

        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="txtlayer_classifier", hub_name="model.json")

        assert os.path.isfile(self.path)
        self.__model = XGBClassifier()
        self.__model.load_model(self.path)

        if get_param_gpu_available(self.config, self.logger):
            gpu_params = dict(predictor="gpu_predictor", tree_method="auto", gpu_id=0)
            self.__model.set_params(**gpu_params)
            self.__model.get_booster().set_param(gpu_params)

        return self.__model

    def predict(self, lines: List[List[LineWithMeta]]) -> np.ndarray:
        result = np.zeros(len(lines))

        idx_list = []
        text_for_inference = []
        for i, line_list in enumerate(lines):
            text_layer = "".join([line.line for line in line_list])
            if not text_layer:
                continue

            if len(text_layer) < 150:
                text_layer = f"\n{text_layer}" * (150 // len(text_layer))
            text_for_inference.append(text_layer)
            idx_list.append(i)

        if not text_for_inference:
            return result

        features = self.feature_extractor.transform(text_for_inference)
        predictions = self.__get_model.predict(features)
        result[idx_list] = predictions
        return result.astype(bool)
