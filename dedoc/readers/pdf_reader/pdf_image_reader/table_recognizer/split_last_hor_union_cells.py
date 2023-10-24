import copy
from typing import List

import numpy as np
from dedocutils.data_structures import BBox

from dedoc.data_structures import ConfidenceAnnotation, LineWithMeta
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_cell_extractor import OCRCellExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_cells


def split_last_column(matrix_table: List[List[Cell]], language: str, image: np.array) -> List[List[Cell]]:
    """
                  A         B       C       D
            --------------------------------------
            |         |  Cell1 | word1            |
            ------------------ |                  |
            |         |  Cell2 | word2            |
            --------------------------------------
             |         |        |        |        |
            --------------------------------------
             |         |        |        |        |
            --------------------------------------

            We need split last union column (C and D position) by y coordinates of column B.
            We don't want simple copy all text "word1\nword2". We want split with correct content. Result below:
            A           B           C         D
            --------------------------------------
            |         |        | word1   | word1  |
            ------------------ |-------- |------- |
            |         |        |  word2  | word1  |
            --------------------------------------
             |         |        |        |        |
            --------------------------------------
             |         |        |        |        |
            --------------------------------------
    """

    if len(matrix_table) == 0 or len(matrix_table[0]) == 0:
        return matrix_table

    last_column = [row[-1] for row in matrix_table]  # get last column
    result_matrix = copy.deepcopy(matrix_table)

    # get union cells
    prev_cell = None
    union_cells = []
    start_union_cell = -1

    for row_id, cell in enumerate(last_column):
        if row_id == 0:
            prev_cell = cell
            union_cells = [prev_cell]
            continue

        if row_id == len(last_column) - 1 and len(union_cells) > 1 or cell.id_con != prev_cell.id_con and len(union_cells) > 1:
            result_matrix[start_union_cell:start_union_cell + len(union_cells)] = \
                _split_each_row(union_cells, matrix_table[start_union_cell:start_union_cell + len(union_cells)], language=language, image=image)
            union_cells = [cell]
            start_union_cell = -1

        if cell.id_con == prev_cell.id_con:
            if start_union_cell == -1:
                start_union_cell = row_id - 1
            union_cells.append(cell)
        else:
            union_cells = [cell]
            start_union_cell = -1

        prev_cell = cell

    return result_matrix


def _split_each_row(union_cells: List[Cell], matrix_table: List[List[Cell]], language: str, image: np.array) -> List[List[Cell]]:
    assert len(union_cells) == len(matrix_table)
    if len(matrix_table[0]) < 1:
        return matrix_table

    row_id = 0
    start_union_cell = -1
    prev_cell = None
    result_matrix = copy.deepcopy(matrix_table)

    # For each row we from the last column find cell in the same id_con (it is the union one cell)

    while row_id < len(matrix_table):
        row = matrix_table[row_id]
        col_id = len(row) - 1

        while col_id > 1:
            cell = row[col_id]
            if col_id == len(row) - 1:
                prev_cell = cell
                union_cells = [prev_cell]
                col_id -= 1
                continue

            if cell.id_con == prev_cell.id_con:
                if start_union_cell == -1:
                    start_union_cell = col_id + 1
                union_cells.append(cell)

            elif len(union_cells) >= 1:
                end_union_cell = col_id + 1
                result_matrix[row_id][end_union_cell:start_union_cell + 1] = \
                    _split_row(cell_splitter=matrix_table[row_id][col_id],
                               union_cell=matrix_table[row_id][end_union_cell:start_union_cell + 1],
                               language=language,
                               image=image)

                union_cells = []
                start_union_cell, end_union_cell = -1, -1
                break

            prev_cell = cell
            col_id -= 1
        row_id += 1
    return result_matrix


def _split_row(cell_splitter: Cell, union_cell: List[Cell], language: str, image: np.array) -> List[Cell]:
    if len(union_cell) == 0:
        return union_cell

    # Get width of all union cell
    eps = len(union_cell)
    x_left = union_cell[0].x_top_left + eps
    x_right = union_cell[-1].x_bottom_right
    # get y coordinate from cell before union cell
    y_top_split = cell_splitter.con_coord.y_top_left
    y_bottom_split = cell_splitter.con_coord.y_top_left + cell_splitter.con_coord.height
    if abs(y_bottom_split - y_top_split) < 10:
        for cell in union_cell:
            cell.lines = []
        return union_cell

    # update y coordinates and text of union cell
    col_id = len(union_cell) - 1
    result_row = copy.deepcopy(union_cell)
    while col_id >= 0:
        union_cell[col_id].y_top_left = y_top_split
        union_cell[col_id].y_bottom_right = y_bottom_split

        cell_image, padding_value = OCRCellExtractor.upscale(image[y_top_split:y_bottom_split, x_left:x_right])
        result_row[col_id].lines = __get_ocr_lines(cell_image, language, page_image=image,
                                                   cell_bbox=BBox(x_top_left=x_left, y_top_left=y_top_split,
                                                                  width=x_right - x_left, height=y_bottom_split - y_top_split),
                                                   padding_cell_value=padding_value)

        col_id -= 1

    return result_row


def __get_ocr_lines(cell_image: np.ndarray, language: str, page_image: np.ndarray, cell_bbox: BBox, padding_cell_value: int) -> List[LineWithMeta]:

    ocr_result = get_text_with_bbox_from_cells(cell_image, language)
    cell_lines = []
    for line in list(ocr_result.lines):
        text_line = OCRCellExtractor.get_line_with_meta("")
        for word in line.words:
            # do absolute coordinate on src_image (inside src_image)
            word.bbox.y_top_left -= padding_cell_value
            word.bbox.x_top_left -= padding_cell_value
            word.bbox.y_top_left += cell_bbox.y_top_left
            word.bbox.x_top_left += cell_bbox.x_top_left

            # add space between words
            if len(text_line) != 0:
                text_line += OCRCellExtractor.get_line_with_meta(" ", bbox=word.bbox, image=page_image)
                # add confidence value

            text_line += OCRCellExtractor.get_line_with_meta(
                text=word.text, bbox=word.bbox, image=page_image,
                confidences=[ConfidenceAnnotation(start=0, end=len(word.text), value=0. if word.confidence < 0 else word.confidence / 100.)]
            )
        if len(text_line) > 0:  # add new line
            cell_lines.append(text_line)

    return cell_lines
