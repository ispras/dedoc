from typing import List

import numpy as np

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier


class LetterTxtlayerClassifier(AbstractTxtlayerClassifier):
    """
    Simple multilingual textual layer correctness classification.
    Textual layer is considered as correct if percent of letters in the text > 50%.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.__symbol_threshold = 0.5

    def predict(self, lines: List[List[LineWithMeta]]) -> np.ndarray:
        texts = np.array(["".join(line.line for line in line_list) for line_list in lines])
        result = np.array([bool(text.strip()) for text in texts])
        ids_for_pred = np.where(result)[0]

        for idx in ids_for_pred:
            text = texts[idx].replace(".", "").replace("…", "")
            letters_number = sum(1 for symbol in text if symbol.isalpha())
            result[idx] = letters_number / max(len(text), 1) > self.__symbol_threshold

        return result
