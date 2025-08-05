import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np

from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractTxtlayerClassifier(ABC):

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

    @abstractmethod
    def predict(self, lines: List[List[LineWithMeta]], parameters: Optional[dict] = None) -> np.ndarray:
        """
        Classifies the correctness of the text layer in a PDF document.

        :param lines: list of lists with document textual lines.
        :returns: array of bool values - True if the textual layer is correct, False otherwise.
        """
        pass
