import gzip
import logging
import os
import pickle
from typing import List

import catboost.core

from dedoc.config import get_config
from dedoc.download_models import download_from_hub
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox


class TxtlayerClassifier:
    """
    The TxtlayerClassifier class is used for classifying the correctness of the text layer in a PDF document.
    """
    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

        eng = list(map(chr, range(ord('a'), ord('z') + 1)))
        rus = [chr(i) for i in range(ord('а'), ord('а') + 32)] + ["ё"]
        digits = [str(i) for i in range(10)]
        special_symbols = [i for i in "<>~!@#$%^&*_+-/\"|?.,:;'`= "]
        brackets = [i for i in "{}[]()"]

        self.letters_list = eng + [i.upper() for i in eng] + rus + [i.upper() for i in rus]
        self.symbols_list = digits + special_symbols + brackets

        self.path = os.path.join(get_config()["resources_path"], "catboost_detect_tl_correctness.pkl.gz")
        self.__model = None

    @property
    def __get_model(self) -> catboost.core.CatBoostClassifier:
        if self.__model is not None:
            return self.__model

        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="catboost_detect_tl_correctness", hub_name="model.pkl.gz")

        assert os.path.isfile(self.path)
        with gzip.open(self.path, 'rb') as f:
            self.__model = pickle.load(f)

        return self.__model

    def predict(self, text_with_bboxes: List[TextWithBBox]) -> bool:
        """
        Classifies the correctness of the text layer in a PDF document.

        :param text_with_bboxes: List of text lines with bounding boxes.
        :returns: True if the text layer is correct, False otherwise.
        """
        text_layer = u"".join([pdf_line.text for pdf_line in text_with_bboxes])
        if not text_layer:
            return False

        features = self.__get_feature_for_predict(text_layer)
        return self.__get_model.predict(features) == 1

    def __get_feature_for_predict(self, text: str) -> List[float]:
        features = []
        num_letters_in_data = self._count_letters(text)
        num_other_symbol_in_data = self._count_other(text)

        for symbol in self.letters_list:
            # proportion of occurring english and russian letters
            features.append(round(text.count(symbol) / num_letters_in_data, 5) if num_letters_in_data != 0 else 0.0)

        for symbol in self.symbols_list:
            # number of symbols
            features.append(text.count(symbol))

        # proportion of letters with symbols
        features.append((num_letters_in_data + num_other_symbol_in_data) / len(text) if len(text) != 0 else 0)
        return features

    def _count_letters(self, text: str) -> int:
        return sum(1 for symbol in text if symbol in self.letters_list)

    def _count_other(self, text: str) -> int:
        return sum(1 for symbol in text if symbol in self.symbols_list)
