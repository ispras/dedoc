from collections import defaultdict
from typing import Dict, Iterable, List

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_block import OcrBlock
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_line import OcrLine
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_paragraph import OcrParagraph
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_tuple import OcrElement


class OcrPage:
    """
    Represents OCR results from the Tesseract. You may see the description in
    https://www.tomrochette.com/tesseract-tsv-format

    Output of the Tesseract has a hierarchical structure:
    Pages (level 1) are divided on Blocks (level 2),
    Blocks are divided on Paragraph (level 3),
    Paragraphs are divided on Lines (level 4)
    Lines are divided on Words (level 5)
    Originally only words have text content, but we will extract text from the lower level

    _______________________________________________________________________________________
    |                                                                                      |
    |   _______________________________________                                            |
    |  |  __________________________________   |                                           |
    |  |  |  line level 4                  |   |                                           |
    |  |  | consists of words level 5      |   |                                           |
    |  |  ---------------------------------    |                                           |
    |  |   paragraph (level 3)                 |                                           |
    |  |                                       |                                           |
    |  |                                       |                                           |
    |  |                                       |                                           |
    |  |                                       |                                           |
    |  |                                       |                                           |
    |  -----------------------------------------                                           |
    |  block (level 2)                                                                     |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    |                                                                                      |
    ----------------------------------------------------------------------------------------
    Page (level 1)
    """

    level = 1

    def __init__(self, blocks: List[OcrBlock]) -> None:
        self.blocks = sorted(blocks, key=lambda block: block.order)

    @property
    def text(self) -> str:
        return "\n".join(blocks.text for blocks in self.blocks)

    @staticmethod
    def from_dict(ocr_dict: Dict[str, List], ocr_conf_thr: float) -> "OcrPage":
        tuples = OcrElement.from_ocr_dict(ocr_dict)
        block2elements = defaultdict(list)
        for element in tuples:
            if element.level > OcrPage.level:
                block2elements[element.block_num].append(element)
        blocks = []
        for key in sorted(block2elements.keys()):
            elements = block2elements[key]
            blocks.append(OcrBlock.from_list(elements, ocr_conf_thr))
        return OcrPage(blocks=blocks)

    @property
    def paragraphs(self) -> Iterable[OcrParagraph]:
        for block in self.blocks:
            for paragraph in block.paragraphs:
                yield paragraph

    @property
    def lines(self) -> Iterable[OcrLine]:
        for paragraph in self.paragraphs:
            for line in paragraph.lines:
                yield line
