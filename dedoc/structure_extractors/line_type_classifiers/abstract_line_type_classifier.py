import abc
from typing import List, Optional

from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractLineTypeClassifier(abc.ABC):
    """
    Abstract class for lines classification with predict method.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        self.config = {} if config is None else config

    @abc.abstractmethod
    def predict(self, lines: List[LineWithMeta]) -> List[str]:
        """
        Predict the line type according to some domain.
        For this purpose, some pretrained classifier may be used.

        :param lines: list of document lines
        :return: list predicted labels for each line
        """
        pass
