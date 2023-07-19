import gzip
import logging
import os
import pickle
from collections import defaultdict
from typing import List

import pandas as pd
from xgboost import XGBClassifier

from dedoc.config import get_config
from dedoc.data_structures import LineWithMeta
from dedoc.download_models import download_from_hub


class TxtlayerFeatureExtractor:

    def __init__(self) -> None:
        eng = list(map(chr, range(ord('a'), ord('z') + 1)))
        rus = [chr(i) for i in range(ord('а'), ord('а') + 32)] + ["ё"]

        self.lower_letters = eng + rus
        self.upper_letters = [i.upper() for i in self.lower_letters]
        self.letters = self.upper_letters + self.lower_letters
        self.digits = [str(i) for i in range(10)]
        self.special_symbols = [i for i in "<>~!@#$%^&*_+-/\"|?.,:;'`= "]
        self.brackets = [i for i in "{}[]()"]
        self.symbols = self.letters + self.digits + self.brackets + self.special_symbols

        self.prohibited_symbols = {s:i for i, s in enumerate(["[", "]", "<"])}

    def transform(self, texts: List[str]) -> pd.DataFrame:
        features = defaultdict(list)

        for text in texts:
            num_letters = self.__count_symbols(text, self.letters)
            num_upper = self.__count_symbols(text, self.upper_letters)
            num_lower = self.__count_symbols(text, self.lower_letters)
            num_digits = self.__count_symbols(text, self.digits)
            num_special_symbols = self.__count_symbols(text, self.special_symbols)
            num_brackets = self.__count_symbols(text, self.brackets)

            features["letters_proportion"].append(num_letters / len(text))
            features["digits_proportion"].append(num_digits / len(text))
            features["special_symbols_proportion"].append(num_special_symbols / len(text))
            features["brackets_proportion"].append(num_brackets / len(text))
            features["lower_letters_proportion"].append(round(num_lower / num_letters, 5) if num_letters != 0 else 0.0)
            features["upper_letters_proportion"].append(round(num_upper / num_letters, 5) if num_letters != 0 else 0.0)

            for symbol in self.letters + self.digits:
                n = num_letters + num_digits
                # proportion of occurring english and russian letters
                features[f"{symbol}_proportion"].append(round(text.count(symbol) / n, 5) if n != 0 else 0.0)

            for symbol in self.special_symbols + self.brackets:
                # number of symbols
                symbol_name = symbol if symbol not in self.prohibited_symbols else f"symbol{self.prohibited_symbols[symbol]}"
                features[f"{symbol_name}_number"].append(text.count(symbol))

            # proportion of letters with symbols
            features["all_proportion"].append((num_letters + num_digits + num_brackets + num_special_symbols) / len(text) if len(text) != 0 else 0)
            features["case_changes"].append(self.__count_case_changes(text))
            features["symbol_changes"].append(self.__count_symbol_changes(text))

        features = pd.DataFrame(features)
        return features[sorted(features.columns)].astype(float)

    def __count_symbols(self, text: str, symbol_list: List[str]) -> int:
        return sum(1 for symbol in text if symbol in symbol_list)

    def __count_case_changes(self, text: str) -> int:
        cnt = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in self.upper_letters) and (s2 in self.lower_letters))
        return cnt

    def __count_symbol_changes(self, text: str) -> int:
        cnt = sum(1 for s1, s2 in zip(text[:-1], text[1:]) if (s1 in self.symbols) != (s2 in self.symbols))
        return cnt


class TxtlayerClassifier:
    """
    The TxtlayerClassifier class is used for classifying the correctness of the textual layer in a PDF document.
    """
    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

        self.feature_extractor = TxtlayerFeatureExtractor()
        # self.path = os.path.join(get_config()["resources_path"], "txtlayer_classifier.pkl.gz")
        self.path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources")),
                                 "txtlayer_classifier.pkl.gz")
        self.__model = None

    @property
    def __get_model(self) -> XGBClassifier:
        if self.__model is not None:
            return self.__model

        if not os.path.isfile(self.path):
            out_dir, out_name = os.path.split(self.path)
            download_from_hub(out_dir=out_dir, out_name=out_name, repo_name="txtlayer_classifier", hub_name="model.pkl.gz")  # TODO

        assert os.path.isfile(self.path)
        with gzip.open(self.path, 'rb') as f:
            self.__model = pickle.load(f)

        return self.__model

    def predict(self, lines: List[LineWithMeta]) -> bool:
        """
        Classifies the correctness of the text layer in a PDF document.

        :param lines: list of document textual lines.
        :returns: True if the textual layer is correct, False otherwise.
        """
        text_layer = u"".join([line.line for line in lines])[:1100]
        if not text_layer:
            return False

        features = self.feature_extractor.transform([text_layer])
        return self.__get_model.predict(features)[0] == 1
