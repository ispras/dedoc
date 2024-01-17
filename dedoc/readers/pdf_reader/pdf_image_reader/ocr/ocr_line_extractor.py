from typing import Iterable, List

import numpy as np

from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.data_classes.word_with_bbox import WordWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_document_page, get_text_with_bbox_from_document_page_one_column


class OCRLineExtractor:

    def __init__(self, *, config: dict) -> None:
        self.config = config

    def split_image2lines(self, image: np.ndarray, page_num: int, language: str = "rus+eng", is_one_column_document: bool = True) -> PageWithBBox:
        bboxes = self.__split_image2bboxes(image=image, page_num=page_num, language=language, is_one_column_document=is_one_column_document)

        filtered_bboxes = list(self._filtered_bboxes(bboxes))
        if len(filtered_bboxes) >= 0:
            new_parsed_doc = PageWithBBox(page_num=page_num, bboxes=filtered_bboxes, image=image)
            return new_parsed_doc

    def __split_image2bboxes(self, image: np.ndarray, page_num: int, language: str, is_one_column_document: bool) -> List[TextWithBBox]:
        ocr_conf_threshold = self.config.get("ocr_conf_threshold", -1)
        if is_one_column_document:
            output_dict = get_text_with_bbox_from_document_page_one_column(image, language, ocr_conf_threshold)
        else:
            output_dict = get_text_with_bbox_from_document_page(image, language, ocr_conf_threshold)

        height, width = image.shape[:2]
        extract_line_bbox = self.config.get("labeling_mode", False)

        lines_with_bbox = []
        for line_num, line in enumerate(output_dict.lines):
            words = [WordWithBBox(text=word.text, bbox=word.bbox) for word in line.words]
            annotations = line.get_annotations(width, height, extract_line_bbox)
            line_with_bbox = TextWithBBox(words=words, page_num=page_num, bbox=line.bbox, line_num=line_num, annotations=annotations)
            lines_with_bbox.append(line_with_bbox)

        return lines_with_bbox

    def _filtered_bboxes(self, bboxes: List[TextWithBBox]) -> Iterable[TextWithBBox]:
        for text_with_bbox in bboxes:
            bbox = text_with_bbox.bbox
            height_width = bbox.height / (bbox.width + 1e-6)
            if 0.01 < height_width < 24:
                yield text_with_bbox
