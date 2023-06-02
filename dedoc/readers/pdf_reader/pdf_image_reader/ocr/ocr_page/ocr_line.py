from typing import List

from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_tuple import OcrElement
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_word import OcrWord


class OcrLine:

    level = 4

    def __init__(self, order: int, bbox: BBox, words: List[OcrWord]) -> None:
        super().__init__()
        self.order = order
        self.bbox = bbox
        self.words = sorted(words, key=lambda word: word.order)

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words if word.text != "") + "\n"

    @staticmethod
    def from_list(line: List[OcrElement], ocr_conf_thr: float) -> "OcrLine":

        words = []
        head = None
        for element in line:
            assert element.level >= OcrLine.level, "get {} in line".format(element)
            if element.level == OcrLine.level:
                head = element
            else:
                words.append(element)
        line = sorted(line, key=lambda word: word.line_num)
        line = list(filter(lambda word: float(word.conf) >= ocr_conf_thr, line))
        ocr_words = [OcrWord(bbox=word.bbox, text=word.text, order=word.word_num) for word in line]
        return OcrLine(order=head.line_num, words=ocr_words, bbox=head.bbox)
