from typing import Dict, List, Optional, Tuple

import numpy as np

from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.utils.utils import flatten


class CellSplitter:
    """
    split merged cells, change table into rectangular

    (0, 0)
     ------------------------------------------> x
     |  ____________________________________________     ____________________________________________
     |  |                      |       B           |     |    A    |    A       |       B           |
     |  |         A            |___________________|     |_________|____________|___________________|
     |  |                      |        C          |     |    A    |     A      |        C          |
     |  |______________________|___________________| ->  |_________|____________|___________________|
     |  |    D    |     E      |       F           |     |    D    |     E      |       F           |
     |  |_________|____________|___________________|     |_________|____________|___________________|
     |  |                G                         |     |    G    |      G     |       G           |
     |  |__________________________________________|     |_________|____________|___________________|
     |
     V  y
    """

    def __init__(self, eps: float = 0.5) -> None:
        self.eps = eps

    def split(self, cells: List[List[Cell]]) -> List[List[Cell]]:
        """
        split merged cells
        """
        if not any(cells):
            return [[]]

        cells_fixed_boarder = self._merge_close_borders(cells=cells)
        horizontal_borders, vertical_borders = self.__get_borders(cells_fixed_boarder)
        horizontal_borders = self.__sort_unique(horizontal_borders)
        vertical_borders = self.__sort_unique(vertical_borders)
        # crate np.array of sorted unique boarders, we will use it to fast split

        column_num = vertical_borders.shape[0] - 1
        row_num = horizontal_borders.shape[0] - 1

        # result matrix, we will fill it later
        result_matrix: List[List[Optional[Cell]]] = [[None] * column_num for _ in range(row_num)]

        # fill the result matrix
        for row in cells_fixed_boarder:
            for cell in row:
                self.__split_one_cell(cell=cell, horizontal_borders=horizontal_borders, result_matrix=result_matrix, vertical_borders=vertical_borders)

        for row_id, row in enumerate(result_matrix):
            for col_id, cell in enumerate(row):
                if cell is None:
                    result_matrix[row_id][col_id] = Cell(x_top_left=horizontal_borders[row_id],
                                                         x_bottom_right=horizontal_borders[row_id + 1],
                                                         y_top_left=vertical_borders[col_id],
                                                         y_bottom_right=vertical_borders[col_id + 1])
        return result_matrix

    @staticmethod
    def __split_one_cell(cell: Cell, horizontal_borders: np.ndarray, vertical_borders: np.ndarray, result_matrix: List[List[Cell]]) -> None:
        left_id, right_id = np.searchsorted(vertical_borders, [cell.x_top_left, cell.x_bottom_right])
        top_id, bottom_id = np.searchsorted(horizontal_borders, [cell.y_top_left, cell.y_bottom_right])
        colspan = right_id - left_id
        rowspan = bottom_id - top_id
        for row_id in range(top_id, bottom_id):
            for column_id in range(left_id, right_id):
                new_cell = Cell.copy_from(cell,
                                          x_top_left=vertical_borders[column_id],
                                          x_bottom_right=vertical_borders[column_id + 1],
                                          y_top_left=horizontal_borders[row_id],
                                          y_bottom_right=horizontal_borders[row_id + 1])
                new_cell.invisible = True
                result_matrix[row_id][column_id] = new_cell

        result_matrix[top_id][left_id].colspan = colspan
        result_matrix[top_id][left_id].rowspan = rowspan
        result_matrix[top_id][left_id].invisible = False

    @staticmethod
    def __sort_unique(borders: List[int]) -> np.ndarray:
        borders = np.array(borders)
        borders.sort()
        borders = np.unique(borders)
        return borders

    @staticmethod
    def __get_border_dict(borders: List[int], threshold: float) -> Dict[int, int]:
        result = {}
        borders.sort()
        current_border = None
        for border in borders:
            if current_border is None or (border - current_border) > threshold:
                current_border = border
            result[border] = current_border
        return result

    def _merge_close_borders(self, cells: List[List[Cell]]) -> List[List[Cell]]:
        """
        merge close borders into one border
        @param cells: table in list of rows form
        @return: cells with merged borders
        """
        horizontal_borders, vertical_borders = self.__get_borders(cells)
        eps_vertical = self.eps * min((cell.width for cell in flatten(cells)), default=0)
        eps_horizontal = self.eps * min((cell.height for cell in flatten(cells)), default=0)
        horizontal_dict = self.__get_border_dict(borders=horizontal_borders, threshold=eps_horizontal)
        vertical_dict = self.__get_border_dict(borders=vertical_borders, threshold=eps_vertical)
        result = []
        for row in cells:
            new_row = []
            for cell in row:
                x_top_left = vertical_dict[cell.x_top_left]
                x_bottom_right = vertical_dict[cell.x_bottom_right]
                y_top_left = horizontal_dict[cell.y_top_left]
                y_bottom_right = horizontal_dict[cell.y_bottom_right]
                if y_top_left < y_bottom_right and x_top_left < x_bottom_right:
                    new_cell = Cell.copy_from(cell, x_top_left=x_top_left, x_bottom_right=x_bottom_right, y_top_left=y_top_left, y_bottom_right=y_bottom_right)
                    new_row.append(new_cell)
            result.append(new_row)
        return result

    @staticmethod
    def __get_borders(cells: List[List[Cell]]) -> Tuple[List[int], List[int]]:
        horizontal_borders = []
        vertical_borders = []
        for row in cells:
            for cell in row:
                horizontal_borders.append(cell.y_top_left)
                horizontal_borders.append(cell.y_bottom_right)
                vertical_borders.append(cell.x_top_left)
                vertical_borders.append(cell.x_bottom_right)
        return horizontal_borders, vertical_borders
