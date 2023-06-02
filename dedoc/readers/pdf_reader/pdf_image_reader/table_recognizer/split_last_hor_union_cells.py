import copy
from typing import List
import numpy as np

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_cell_extractor import OCRCellExtractor
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.utils import get_cell_text_by_ocr


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

        if row_id == len(last_column) - 1 and len(union_cells) > 1 or \
                cell.id_con != prev_cell.id_con and len(union_cells) > 1:
            result_matrix[start_union_cell:start_union_cell + len(union_cells)] = \
                _split_each_row(union_cells, matrix_table[start_union_cell:start_union_cell + len(union_cells)],
                                language=language,
                                image=image)
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


def _split_each_row(union_cells: List[Cell], matrix_table: List[List[Cell]], language: str, image: np.array) \
        -> List[List[Cell]]:
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
            cell.text = ""
        return union_cell

    # update y coordinates and text of union cell
    col_id = len(union_cell) - 1
    result_row = copy.deepcopy(union_cell)
    while col_id >= 0:
        union_cell[col_id].y_top_left = y_top_split
        union_cell[col_id].y_bottom_right = y_bottom_split

        cell_image = OCRCellExtractor.upscale(image[y_top_split:y_bottom_split, x_left:x_right])
        result_row[col_id].text = get_cell_text_by_ocr(cell_image, language=language)

        col_id -= 1

    return result_row
