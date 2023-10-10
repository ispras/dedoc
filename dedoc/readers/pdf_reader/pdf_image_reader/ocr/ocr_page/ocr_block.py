from collections import defaultdict
from typing import List

from dedocutils.data_structures import BBox

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_paragraph import OcrParagraph
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_tuple import OcrElement


class OcrBlock:
    level = 2

    def __init__(self, order: int, bbox: BBox, paragraphs: List[OcrParagraph]) -> None:
        super().__init__()
        self.order = order
        self.bbox = bbox
        self.paragraphs = paragraphs

    @property
    def text(self) -> str:
        return "".join(paragraph.text for paragraph in self.paragraphs)

    @staticmethod
    def from_list(elements: List[OcrElement], ocr_conf_thr: float) -> "OcrBlock":
        paragraph2elements = defaultdict(list)
        head = None
        for element in elements:
            if element.level > OcrBlock.level:
                paragraph2elements[element.paragraph_num].append(element)
            elif element.level == OcrBlock.level:
                head = element
            else:
                raise ValueError(f"Some element {element} has level greater than this {OcrBlock.level}")
        paragraphs = [OcrParagraph.from_list(paragraph2elements[key], ocr_conf_thr) for key in sorted(paragraph2elements.keys())]
        return OcrBlock(paragraphs=paragraphs, order=head.block_num, bbox=head.bbox)
