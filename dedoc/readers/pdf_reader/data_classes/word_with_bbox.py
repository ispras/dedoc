from collections import OrderedDict

from dedocutils.data_structures import BBox


class WordWithBBox:

    def __init__(self, bbox: BBox, text: str) -> None:
        self.bbox = bbox
        self.text = text

    def __str__(self) -> str:
        return f"WordWithBBox(bbox = {self.bbox}, text = {self.text})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict:
        res = OrderedDict()
        res["bbox"] = self.bbox.to_dict()
        res["text"] = self.text
        return res
