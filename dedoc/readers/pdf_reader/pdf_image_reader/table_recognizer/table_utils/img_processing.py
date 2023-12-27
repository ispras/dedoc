import logging
import math
import os
from typing import Any, List, Tuple

import cv2
import imutils
import numpy as np

from dedoc.config import get_config
from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
from dedoc.readers.pdf_reader.data_classes.tables.table_type import TableTypeAdditionalOptions
from dedoc.utils.parameter_utils import get_path_param

logger = get_config().get("logger", logging.getLogger())
table_options = TableTypeAdditionalOptions()

ROTATE_THRESHOLD = 0.3


def rotate_with_threshold(img: np.ndarray, angle: float, threshold: float = None, *, config: dict) -> np.ndarray:
    """rotates a table image and saving image.shape during rotation. It is important for word bounding box extraction"""
    if threshold is None:
        threshold = ROTATE_THRESHOLD
    rotated = img
    if abs(angle) > threshold:
        if config.get("debug_mode", False):
            logger.debug("rotated image")
        rotated = imutils.rotate(img, angle)
    return rotated


# Algorithm for finding lines by Houph. Allows you to eliminate gaps between lines and find the angle of the table
def apply_houph_line(img: np.ndarray, threshold_gap: int = 10, *, config: dict) -> Tuple[np.ndarray, int]:
    cdst_p = np.copy(img)
    dst = abs(img - 255)
    lines_p = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, 100, 300, threshold_gap)

    k_hor = []

    if lines_p is not None:
        for i in range(0, len(lines_p)):
            line = lines_p[i][0]
            # k - angle of line in degree
            if abs(line[0] - line[2]) == 0:
                k = math.atan(0) * 180.0 / math.pi
            else:
                k = math.atan((line[1] - line[3]) / (line[0] - line[2])) * 180.0 / math.pi

            if abs(k) < 5:
                k_hor.append(k)
                cv2.line(cdst_p, (line[0], line[1]), (line[2], line[3]), (0, 0, 255), 1, cv2.LINE_AA)
            if (abs(k) < 95) and (abs(k) > 85):
                cv2.line(cdst_p, (line[0], line[1]), (line[2], line[3]), (0, 0, 255), 1, cv2.LINE_AA)

    angle = np.sum(k_hor) / len(k_hor) if len(k_hor) > 0 else 0

    if math.isnan(angle):
        angle = 0

    if config.get("debug_mode", False):
        logger.debug(f"angle_horiz_avg = {angle}")

    return cdst_p, angle


def get_contours_cells(img: np.ndarray, table_type: str, *, config: dict) -> [Any, Any, np.ndarray, float]:
    """
    function's steps:
    1) detects Houph lines for detecting rotate angle. Then input image has rotated on the rotate angle.
    2) performs morphological operations under rotated images for detecting horizontal and vertical lines
    3) on found lines detects tree contours with help cv2.findContours
    :param img: input image
    :param config: dict from config.py
    :return: contours, contours's hierarchy, rotated image, rotate angle
    """

    # Thresholding the image
    (thresh, img_bin) = cv2.threshold(img, 225, 255, cv2.THRESH_BINARY)
    # step 1 - Invert the image
    img_bin = 255 - img_bin

    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "image_bin.jpg"), img_bin)
    # step 2
    img_final_bin = __detect_horizontal_and_vertical_lines(img_bin, config, "tables")
    # step 3
    img_final_bin_houph, angle_alignment = __apply_houph_lines_and_detect_angle(img_final_bin, config)

    (thresh, img_final_bin_houph) = cv2.threshold(img_final_bin_houph, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_final_bin.jpg"), img_final_bin)
    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_final_bin_houph.jpg"), img_final_bin_houph)

    # step 4 - rotating
    img_final_bin_houph = rotate_with_threshold(img_final_bin_houph, angle_alignment, config=config)
    img = rotate_with_threshold(img, angle_alignment, config=config)
    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "aligned_img.jpg"), img)
    img_final_bin_houph = __paint_bounds(img_final_bin_houph)

    # step 5  - detect contours
    contours, hierarchy = cv2.findContours(img_final_bin_houph, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)

    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_houph_and_morph_wo_bound.jpg"), img_final_bin_houph)
        img_w_contour = img.copy()
        cv2.drawContours(img_w_contour, contours, contourIdx=-1, color=(0, 0, 0), thickness=10, hierarchy=hierarchy, maxLevel=8)
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_with_contours.jpg"), img_w_contour)

    # Draw external contours for tables without external contours. It is a rare case, but important for invoices
    if table_options.table_wo_external_bounds in table_type:
        contours, hierarchy = __get_contours_for_table_wo_external_bounds(img, img_final_bin_houph.copy(), contours, hierarchy, config)
    return contours, hierarchy, img, angle_alignment


def __get_contours_for_table_wo_external_bounds(img: np.ndarray, img_with_contours: np.ndarray, contours: List, hierarchy: List, config: dict) -> [Any, Any]:
    # get children (get table counters)
    contours = np.array(contours)
    list_contours, table_contours = __get_table_contours(contours, hierarchy)

    filtered_cont_id = []
    for i, c in enumerate(table_contours):
        # Returns the location and width,height for table contour
        x, y, w, h = cv2.boundingRect(c)
        table_image = img[y:y + h, x:x + w]

        # filter contours which not similar a table contour
        if not __filter_table(img, table_image):
            filtered_cont_id.append(list_contours[i])

    if len(filtered_cont_id) == 0:
        return contours, hierarchy

    for c in contours[np.array(filtered_cont_id)]:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(img_with_contours, (x, y), (x + w, y + h), color=(0, 0, 0), thickness=5)

    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_with_external_bounds.jpg"), img_with_contours)
    contours, hierarchy = cv2.findContours(img_with_contours, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)

    return contours, hierarchy


def __filter_table(image: np.ndarray, table_image: np.ndarray) -> bool:
    mean = table_image.mean()
    std = table_image.std()
    white_mean = (table_image > 225).mean()
    black_mean = (table_image < 225).mean()
    table_area = table_image.shape[0] * table_image.shape[1]
    image_area = image.shape[0] * image.shape[1]

    res = (white_mean < 0.5) or (black_mean > 0.3) or (std < 30) or (mean < 150) or (mean < 200 and std < 80) or (table_area < image_area * 0.2)
    return res


def __get_table_contours(contours: np.ndarray, hierarchy: List) -> [np.ndarray, np.ndarray]:
    list_contours = np.array([h_id for h_id, h in enumerate(hierarchy[0]) if h[3] == 0], dtype=int)

    return list_contours, contours[list_contours]


def __apply_houph_lines_and_detect_angle(image: np.ndarray, config: dict) -> [np.ndarray, float]:
    # ----- search height, width table ----- #
    # ----- detect gap for houph -------     #
    contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    contours_table = [cv2.boundingRect(c) for ind, c in enumerate(contours) if hierarchy[0][ind][3] == 0 and hierarchy[0][ind][2] != -1]  # List[[x,y,w,h]]
    if len(contours_table) > 0:
        gap_avg = min(np.mean([c[3] for c in contours_table]) // 35, 100)
        gap_avg = min(np.mean([c[2] for c in contours_table]) // 45, gap_avg)
    else:
        gap_avg = 5
    if config.get("debug_mode", False):
        config.get("logger", logging.getLogger()).debug(f"Houph gap = {gap_avg}")

    # ----- image alignment -----
    # Houph apply
    img_final_bin_houph, angle_alignment = apply_houph_line(image, gap_avg, config=config)

    return img_final_bin_houph, angle_alignment


def __detect_horizontal_and_vertical_lines(img_bin: np.ndarray, config: dict, task: str) -> np.ndarray:
    # Defining a kernel length

    if task == "orientation":
        length_div = 13
        height_div = 13
    elif task == "tables":
        length_div = 55
        height_div = 100

    kernel_length_weight = max(np.array(img_bin).shape[1] // length_div, TableTree.min_w_cell)  # 35
    kernel_length_height = max(np.array(img_bin).shape[0] // height_div, TableTree.min_h_cell)  # 100

    # A verticle kernel of (1 X kernel_length), which will detect all the verticle lines from the image.
    verticle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length_height))
    # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
    hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length_weight, 1))

    # A kernel of (3 X 3) ones.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    # Morphological operation to detect vertical and horizontal lines from an image
    iterations = 2

    img_temp1 = cv2.erode(img_bin, verticle_kernel, iterations=iterations)
    verticle_lines_img = cv2.dilate(img_temp1, verticle_kernel, iterations=iterations)
    img_temp2 = cv2.erode(img_bin, hori_kernel, iterations=iterations)
    horizontal_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=iterations)

    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "verticle_lines.jpg"), verticle_lines_img)
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "horizontal_lines.jpg"), horizontal_lines_img)

    """Now we will add these two images.
    This will have only boxes and the information written in the box will be erased.
    So we can accurately detect the boxes and no noise will occur for false box extraction
    """
    # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
    alpha = 0.5
    beta = 1.0 - alpha

    # This function helps to add two image with specific weight
    # parameter to get a third image as summation of two image.
    img_bin_with_lines = cv2.addWeighted(verticle_lines_img, alpha, horizontal_lines_img, beta, 0.0)
    img_bin_with_lines = cv2.erode(~img_bin_with_lines, kernel, iterations=2)
    (thresh, img_bin_with_lines) = cv2.threshold(img_bin_with_lines, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    if config.get("debug_mode", False):
        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_bin_with_lines.jpg"), img_bin_with_lines)

    return img_bin_with_lines


def __paint_bounds(image: np.ndarray) -> np.ndarray:
    # Paints over the borders formed by rotation
    color_backgr = np.max(image)
    bound_w = 5
    image[0:bound_w, :] = color_backgr
    image[-bound_w:, :] = color_backgr
    image[:, 0:bound_w] = color_backgr
    image[:, -bound_w:] = color_backgr

    return image


def detect_tables_by_contours(img: np.ndarray,
                              language: str = "rus",
                              orient_analysis_cells: bool = False,
                              table_type: str = "",
                              *,
                              config: dict) -> [TableTree, List[np.ndarray], float]:
    """
    detecting contours and TreeTable with help contour analysis. TreeTable is
    :param orient_analysis_cells:
    :param img: input image
    :param language: parameter language for Tesseract
    :param config: dict from config.py
    :return: TreeTable, contour, rotate angle
    """
    contours, hierarchy, image, angle_rotate = get_contours_cells(img, table_type, config=config)
    tree_table = TableTree.parse_contours_to_tree(contours=contours, hierarchy=hierarchy, config=config)

    if config.get("debug_mode", False):
        config.get("logger", logging.getLogger()).debug(f"Hierarchy [Next, Previous, First_Child, Parent]:\n {hierarchy}")
        tree_table.print_tree(depth=0)

        cv2.imwrite(os.path.join(get_path_param(config, "path_detect"), "img_draw_counters.jpg"), img)

    tree_table.set_text_into_tree(tree=tree_table, src_image=image, language=language, config=config)

    if config.get("debug_mode", False):
        tree_table.print_tree(depth=0)

    return tree_table, contours, angle_rotate
