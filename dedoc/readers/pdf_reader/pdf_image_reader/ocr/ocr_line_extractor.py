import concurrent.futures
from collections import namedtuple
from typing import Iterable, Iterator, List

import numpy as np

from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_document_page, \
    get_text_with_bbox_from_document_page_one_column

BBoxLevel = namedtuple("BBoxLevel", ["text_line", "some_word"])
bbox_level = BBoxLevel(4, 5)


class OCRLineExtractor:

    def __init__(self, *, config: dict) -> None:
        self.config = config

    def split_image2lines(self,
                          image: np.ndarray,
                          page_num: int,
                          language: str = "rus+eng",
                          is_one_column_document: bool = True) -> PageWithBBox:
        bboxes = self.__split_image2bboxes(image=image, page_num=page_num, language=language, is_one_column_document=is_one_column_document)

        filtered_bboxes = list(self._filtered_bboxes(bboxes))
        if len(filtered_bboxes) >= 0:
            new_parsed_doc = PageWithBBox(page_num=page_num, bboxes=filtered_bboxes, image=image)
            return new_parsed_doc
    """
    def split_imagecell2lines(self,
                          cell_image: np.ndarray,
                          page_num: int,
                          page_height: int,
                          page_width: int,
                          language: str = "rus+eng",) -> PageWithBBox:
        bboxes = self.__split_image2bboxes_from_cell(cell_image=cell_image, page_num=page_num, language=language, page_height=page_height,
        page_width=page_width)

        filtered_bboxes = list(self._filtered_bboxes(bboxes))
        if len(filtered_bboxes) >= 0:
            new_parsed_cell = PageWithBBox(page_num=page_num, bboxes=filtered_bboxes, image=cell_image)
            return new_parsed_cell"""

    def split_images2lines(self, images: Iterator[np.ndarray], language: str = "rus+eng") -> List[PageWithBBox]:
        input_data = ((page, image, language) for page, image in enumerate(images))
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.config["n_jobs"]) as executor:
            documents = executor.map(self._parse_one_image, input_data)

        return [doc for doc in documents if doc is not None]

    def _parse_one_image(self, args: List) -> PageWithBBox:
        page_num, image, language = args
        bboxes = self.__split_image2bboxes(image=image, page_num=page_num, language=language, is_one_column_document=True)
        if len(bboxes) > 0:
            new_parsed_doc = PageWithBBox(page_num=page_num, bboxes=bboxes, image=image)
            return new_parsed_doc

    @staticmethod
    def _is_box_in(box1: BBox, box2: BBox) -> bool:
        """
        check if box1 is in box2
        """
        x_inside = (box1.x_top_left >= box2.x_top_left) and (box1.x_bottom_right <= box2.x_bottom_right)
        y_inside = (box1.y_top_left >= box2.y_top_left) and (box1.y_bottom_right <= box2.y_bottom_right)
        return x_inside and y_inside

    def __split_image2bboxes(self, image: np.ndarray, page_num: int, language: str, is_one_column_document: bool) -> List[TextWithBBox]:
        ocr_conf_threshold = self.config.get("ocr_conf_threshold", -1)
        if is_one_column_document:
            output_dict = get_text_with_bbox_from_document_page_one_column(image, language, ocr_conf_threshold)
        else:
            output_dict = get_text_with_bbox_from_document_page(image, language, ocr_conf_threshold)

        height, width = image.shape[:2]
        line_boxes = [TextWithBBox(text=line.text, page_num=page_num, bbox=line.bbox, line_num=line_num, annotations=line.get_annotations(width, height))
                      for line_num, line in enumerate(output_dict.lines)]

        return line_boxes

    """def __split_image2bboxes_from_cell(self, cell_image: np.ndarray, page_num: int, language: str, page_height: int, page_width: int) -> List[TextWithBBox]
        output_dict = get_text_with_bbox_from_cells(cell_image, language, ocr_conf_threshold=0.0)
        line_boxes = [
            TextWithBBox(text=line.text, page_num=page_num, bbox=line.bbox, line_num=line_num, annotations=line.get_annotations(page_width, page_height))
            for line_num, line in enumerate(output_dict.lines)]

        return line_boxes"""

    def _filtered_bboxes(self, bboxes: List[TextWithBBox]) -> Iterable[TextWithBBox]:
        for text_with_bbox in bboxes:
            bbox = text_with_bbox.bbox
            height_width = bbox.height / (bbox.width + 1e-6)
            if 0.01 < height_width < 24:
                yield text_with_bbox
