import abc
from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta


class AbstractLineTypeClassifier(abc.ABC):

    document_type = None

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.chunk_start_tags = ["header", "body"]
        self.hl_type = ""
        self._chunk_hl_builders = []

    @abc.abstractmethod
    def predict(self, lines: List[LineWithMeta]) -> List[str]:
        """
        :param lines: image and bboxes with text, it is useful for feature extraction and label predictions
        :return: lines with metadata and predicted labels and hierarchy levels
        """
        pass

    def get_chunk_start_tags(self) -> List[str]:
        return self.chunk_start_tags

    def get_hl_type(self) -> str:
        return self.hl_type
