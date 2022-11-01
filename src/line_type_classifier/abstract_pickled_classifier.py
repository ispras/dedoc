import abc
import gzip
import pickle

from src.line_type_classifier.abstract_scan_classifier import AbstractLineTypeClassifier


class AbstractPickledLineTypeClassifier(AbstractLineTypeClassifier):

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    @staticmethod
    @abc.abstractmethod
    def load_pickled(path: str, *, config: dict) -> AbstractLineTypeClassifier:
        pass

    def _save2pickle(self, path_out: str, parameters: object) -> str:
        if path_out.endswith(".pkl"):
            path_out += ".gz"
        elif path_out.endswith(".gz"):
            pass
        else:
            path_out += ".pkl.gz"
        with gzip.open(path_out, "wb") as file_out:
            pickle.dump(obj=parameters, file=file_out)
        return path_out
