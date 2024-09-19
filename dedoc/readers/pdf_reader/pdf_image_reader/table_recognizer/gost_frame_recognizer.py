import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from dedocutils.data_structures import BBox

from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.img_processing import detect_horizontal_and_vertical_lines as detect_lines

MIN_FRAME_CONTENT_AREA = 0.65


class GOSTFrameRecognizer:
    def __init__(self, *, config: dict = None) -> None:
        self.logger = config.get("logger", logging.getLogger())
        self.config = config

    def rec_and_clean_frame(self, image: np.ndarray) -> Tuple[np.ndarray, BBox, Tuple[int, ...]]:
        if len(image.shape) < 3:  # check if an image is already converted to grayscale
            thresh, img_bin = cv2.threshold(image, 225, 255, cv2.THRESH_BINARY)
        else:
            thresh, img_bin = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 225, 255, cv2.THRESH_BINARY)
        lines_bin = detect_lines(255 - img_bin, self.config, "tables")
        contours, hierarchy = cv2.findContours(lines_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
        tree_table = TableTree.parse_contours_to_tree(contours=contours, hierarchy=hierarchy, config=self.config)

        img_area = image.shape[0] * image.shape[1]
        has_gost_frame, main_box = self._analyze_cells_on_frame(tree_table, img_area)
        if has_gost_frame:
            return BBox.crop_image_by_box(image, main_box), main_box, (int(image.shape[0]), int(image.shape[1]))
        return image, BBox(0, 0, image.shape[1], image.shape[0]), (int(image.shape[0]), int(image.shape[1]))

    def _analyze_cells_on_frame(self, tree_table: "TableTree", img_area: "int") -> Tuple[bool, Optional[BBox]]:
        try:
            sub_bboxes = tree_table.children[0].children
            for box in sub_bboxes:
                if box.cell_box.square / img_area > MIN_FRAME_CONTENT_AREA:
                    return True, box.cell_box
            return False, None
        except Exception as ex:
            self.logger.warning(ex)
            return False, None
