import os
from typing import List

import numpy as np

from dedoc.config import get_config
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier


class LanguageTxtlayerClassifier(AbstractTxtlayerClassifier):
    """
    Simple multilingual textual layer correctness classification.
    The textual layer is considered as a correct if its language was detected with probability > 50%.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.path = os.path.join(get_config()["resources_path"], "language_detector.bin")
        self.__model = None

    @property
    def model(self):  # noqa
        if self.__model is not None:
            return self.__model

        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="language_detector", hub_name="language_detector.bin")

        assert os.path.isfile(self.path)

        import fasttext
        self.__model = fasttext.load_model(self.path)
        return self.__model

    def predict(self, lines: List[List[LineWithMeta]]) -> np.ndarray:
        texts = [" ".join(line.line for line in line_list).replace("\n", " ") for line_list in lines]
        predictions = self.model.predict(texts, threshold=0.5)
        predictions = np.array([any(pred) for pred in predictions[1]], dtype=bool)
        return predictions
