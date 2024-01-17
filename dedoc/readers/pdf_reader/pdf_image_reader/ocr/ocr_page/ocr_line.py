from typing import List

from dedocutils.data_structures import BBox

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.confidence_annotation import ConfidenceAnnotation
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

    def get_annotations(self, page_width: int, page_height: int, extract_line_bbox: bool) -> List[Annotation]:
        if extract_line_bbox:
            return [BBoxAnnotation(0, len(" ".join([w.text for w in self.words])), self.bbox, page_width, page_height)]

        start = 0
        annotations = []

        for word in self.words:
            if word.text == "":
                continue

            end = start + len(word.text)
            annotations.append(ConfidenceAnnotation(start, end, str(word.confidence / 100)))
            annotations.append(BBoxAnnotation(start, end, word.bbox, page_width, page_height))
            start += len(word.text) + 1

        return annotations

    @staticmethod
    def from_list(line: List[OcrElement], ocr_conf_thr: float) -> "OcrLine":

        words = []
        head = None
        for element in line:
            assert element.level >= OcrLine.level, f"get {element} in line"
            if element.level == OcrLine.level:
                head = element
            else:
                words.append(element)
        line = sorted(line, key=lambda word: word.line_num)
        line = list(filter(lambda word: float(word.conf) >= ocr_conf_thr, line))
        ocr_words = [OcrWord(bbox=word.bbox, text=word.text, confidence=word.conf, order=word.word_num) for word in line]
        return OcrLine(order=head.line_num, words=ocr_words, bbox=head.bbox)
