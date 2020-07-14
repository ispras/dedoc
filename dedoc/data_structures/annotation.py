from collections import OrderedDict

from dedoc.data_structures.serializable import Serializable


class Annotation(Serializable):

    def __init__(self, start: int, end: int, value: str):
        """
        Some kind of text information about symbols between start and end. For example Annotation(1, 13, "italic")
        says that text between 1st and 13st symbol was writen in italic

        :param start: annotated text start
        :param end: annotated text end
        :param value: information about annotated text
        """

        self.start = start
        self.end = end
        self.value = value

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["start"] = self.start
        res["end"] = self.end
        res["value"] = self.value
        return res
