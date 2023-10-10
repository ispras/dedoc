from typing import Dict, Iterable

from dedocutils.data_structures import BBox


class OcrElement:
    """
    represents one line of the Tesseract tsv file
    """

    def __init__(self,
                 page_num: int,
                 left: int,
                 level: int,
                 par_num: int,
                 line_num: int,
                 text: str,
                 width: int,
                 conf: float,
                 top: int,
                 word_num: int,
                 height: int,
                 block_num: int) -> None:
        self.page_num = page_num
        self.left = left
        self.level = level
        self.paragraph_num = par_num
        self.line_num = line_num
        self.text = text
        self.width = width
        self.conf = conf
        self.top = top
        self.word_num = word_num
        self.height = height
        self.block_num = block_num

    def __str__(self) -> str:
        return f"OcrTUPLE(level={self.level}, conf={self.conf}, text={self.text[:60]})"

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def from_ocr_dict(ocr_dict: Dict[str, list]) -> Iterable["OcrElement"]:
        keys = list(ocr_dict.keys())
        size = len(ocr_dict[keys[0]])
        for key in keys:
            assert size == len(ocr_dict[key])
        for i in range(size):
            yield OcrElement(**{key: ocr_dict[key][i] for key in keys})

    @property
    def bbox(self) -> BBox:
        return BBox(x_top_left=self.left, y_top_left=self.top, width=self.width, height=self.height)
