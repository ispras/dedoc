import json
import re
from typing import IO, List, Match, Optional, Tuple

import cv2
import numpy as np
from pdfminer.layout import LTContainer
from pdfminer.pdfpage import PDFPage

from dedoc.data_structures.bbox import BBox
from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation


def draw_layout_element(image_src: np.ndarray,
                        lobjs: List,
                        file: IO,
                        k_w: float,
                        k_h: float,
                        page: PDFPage,
                        color: Tuple[int, int, int],
                        text: Optional[str] = None) -> None:
    for lobj in lobjs:
        # converting coordinate from pdf format into image
        box_lobj = convert_coordinates_pdf_to_image(lobj, k_w, k_h, int(page.mediabox[3]))

        cv2.rectangle(image_src, (box_lobj.x_top_left, box_lobj.y_top_left), (box_lobj.x_bottom_right, box_lobj.y_bottom_right), color)

        if text is not None:
            cv2.putText(image_src, text, (box_lobj.x_top_left, box_lobj.y_top_left), cv2.FONT_HERSHEY_SIMPLEX, 1, color)
        else:
            file.write(lobj.get_text())


def draw_annotation(image: np.ndarray, annotations: List[BBoxAnnotation]) -> None:
    for ann in annotations:
        bbox = json.loads(ann.value)
        p1 = (int(bbox["x_top_left"] * bbox["page_width"]), int(bbox["y_top_left"] * bbox["page_height"]))
        p2 = (int((bbox["x_top_left"] + bbox["width"]) * bbox["page_width"]), int((bbox["y_top_left"] + bbox["height"]) * bbox["page_height"]))
        cv2.rectangle(image, p1, p2, (0, 255, 0))


def convert_coordinates_pdf_to_image(lobj: LTContainer, k_w: float, k_h: float, height_page: int) -> BBox:
    x0 = int(lobj.x0 * k_w)
    x1 = int(lobj.x1 * k_w)
    y0 = int((height_page - lobj.y1) * k_h)
    y1 = int((height_page - lobj.y0) * k_h)

    return BBox(x0, y0, x1 - x0, y1 - y0)


def create_bbox(height: int, k_h: float, k_w: float, lobj: LTContainer) -> BBox:
    curr_box_line = convert_coordinates_pdf_to_image(lobj, k_w, k_h, height)
    bbox = BBox.from_two_points((curr_box_line.x_top_left, curr_box_line.y_top_left), (curr_box_line.x_bottom_right, curr_box_line.y_bottom_right))
    return bbox


def cleaning_text_from_hieroglyphics(text_str: str) -> str:
    """
    replace all cid-codecs into ascii symbols. cid-encoding - hieroglyphic fonts
    :param text_str: text
    :return: text wo cids-chars
    """
    return re.sub(r"\(cid:(\d)*\)", cid_to_ascii_text, text_str)


def cid_to_ascii_text(m: Match) -> str:
    v = m.group(0)
    v = v.strip("(").strip(")")
    ascii_num = v.split(":")[-1]
    ascii_num = int(ascii_num)
    text_value = chr(ascii_num)

    return text_value
