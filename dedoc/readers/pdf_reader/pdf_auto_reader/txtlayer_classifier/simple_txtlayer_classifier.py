from typing import List

import numpy as np

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier


class SimpleTxtlayerClassifier(AbstractTxtlayerClassifier):
    """
    Simple textual layer correctness classification.
    The textual layer is considered as a correct if it isn't empty.
    """

    def predict(self, lines: List[List[LineWithMeta]]) -> np.ndarray:
        result = np.array([any(line.line.strip() for line in line_list) for line_list in lines])
        return result
