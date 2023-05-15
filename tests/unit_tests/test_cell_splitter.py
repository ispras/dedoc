import unittest

from dedoc.readers.scanned_reader.data_classes.tables.cell import Cell
from dedoc.readers.scanned_reader.table_recognizer.cell_splitter import CellSplitter


class TestCellSplitter(unittest.TestCase):
    splitter = CellSplitter()

    def test__merge_close_borders(self) -> None:
        cells = [
            [Cell(x_top_left=0, y_top_left=0, x_bottom_right=50, y_bottom_right=30),
             Cell(x_top_left=51, y_top_left=2, x_bottom_right=90, y_bottom_right=29)],
            [Cell(x_top_left=0, y_top_left=31, x_bottom_right=50, y_bottom_right=50),
             Cell(x_top_left=51, y_top_left=31, x_bottom_right=91, y_bottom_right=50)]
        ]
        cells_merged = self.splitter._merge_close_borders(cells)
        self.assertEqual(0, cells_merged[0][0].x_top_left)
        self.assertEqual(0, cells_merged[0][0].y_top_left)
        self.assertEqual(50, cells_merged[0][0].x_bottom_right)
        self.assertEqual(29, cells_merged[0][0].y_bottom_right)

        self.assertEqual(50, cells_merged[0][1].x_top_left)
        self.assertEqual(0, cells_merged[0][1].y_top_left)
        self.assertEqual(90, cells_merged[0][1].x_bottom_right)
        self.assertEqual(29, cells_merged[0][1].y_bottom_right)

        self.assertEqual(0, cells_merged[1][0].x_top_left)
        self.assertEqual(29, cells_merged[1][0].y_top_left)
        self.assertEqual(50, cells_merged[1][0].x_bottom_right)
        self.assertEqual(50, cells_merged[1][0].y_bottom_right)

        self.assertEqual(50, cells_merged[1][1].x_top_left)
        self.assertEqual(29, cells_merged[1][1].y_top_left)
        self.assertEqual(90, cells_merged[1][1].x_bottom_right)
        self.assertEqual(50, cells_merged[1][1].y_bottom_right)

    def test__merge_close_borders_one_cell(self) -> None:
        cells = [[Cell(x_top_left=0, y_top_left=0, x_bottom_right=50, y_bottom_right=30)]]
        cells_merged = self.splitter._merge_close_borders(cells)
        self.assertEqual(0, cells_merged[0][0].x_top_left)
        self.assertEqual(0, cells_merged[0][0].y_top_left)
        self.assertEqual(50, cells_merged[0][0].x_bottom_right)
        self.assertEqual(30, cells_merged[0][0].y_bottom_right)

    def test__merge_close_borders_none_cells(self) -> None:
        cells = [[]]
        cells_merged = self.splitter._merge_close_borders(cells)
        self.assertListEqual([[]], cells_merged)

    def test_split_zero_cells(self) -> None:
        cells = [[]]
        matrix = self.splitter.split(cells=cells)
        self.assertListEqual([[]], matrix)

    def test_split_one_cell(self) -> None:
        cells = [[Cell(x_top_left=0, y_top_left=0, x_bottom_right=10, y_bottom_right=15)]]
        matrix = self.splitter.split(cells=cells)
        self.assertEqual(1, len(matrix))
        self.assertEqual(1, len(matrix[0]))
        new_cell = matrix[0][0]
        self.assertEqual(0, new_cell.x_top_left)
        self.assertEqual(0, new_cell.y_top_left)
        self.assertEqual(10, new_cell.x_bottom_right)
        self.assertEqual(15, new_cell.y_bottom_right)

    def test_horizontal_split(self) -> None:
        cells = [
            [
                Cell(x_top_left=0, y_top_left=0, x_bottom_right=3, y_bottom_right=5),
                Cell(x_top_left=3, y_top_left=0, x_bottom_right=7, y_bottom_right=3),
            ],
            [
                Cell(x_top_left=3, y_top_left=3, x_bottom_right=7, y_bottom_right=5),
            ]
        ]
        matrix = self.splitter.split(cells)
        self.assertEqual(2, len(matrix))
        self.assertEqual(2, len(matrix[0]))
        self.assertEqual(2, len(matrix[1]))
        [cell_a, cell_b], [cell_c, cell_d] = matrix
        self.assertEqual(0, cell_a.x_top_left)
        self.assertEqual(0, cell_a.y_top_left)
        self.assertEqual(3, cell_a.x_bottom_right)
        self.assertEqual(3, cell_a.y_bottom_right)

        self.assertEqual(3, cell_b.x_top_left)
        self.assertEqual(0, cell_b.y_top_left)
        self.assertEqual(7, cell_b.x_bottom_right)
        self.assertEqual(3, cell_b.y_bottom_right)

        self.assertEqual(0, cell_c.x_top_left)
        self.assertEqual(3, cell_c.y_top_left)
        self.assertEqual(3, cell_c.x_bottom_right)
        self.assertEqual(5, cell_c.y_bottom_right)

        self.assertEqual(3, cell_d.x_top_left)
        self.assertEqual(3, cell_d.y_top_left)
        self.assertEqual(7, cell_d.x_bottom_right)
        self.assertEqual(5, cell_d.y_bottom_right)

    def test_vertical_split(self) -> None:
        cells = [
            [
                Cell(x_top_left=0, y_top_left=0, x_bottom_right=8, y_bottom_right=2),
            ],
            [
                Cell(x_top_left=0, y_top_left=2, x_bottom_right=5, y_bottom_right=5),
                Cell(x_top_left=5, y_top_left=2, x_bottom_right=8, y_bottom_right=5),
            ]
        ]
        matrix = self.splitter.split(cells)
        self.assertEqual(2, len(matrix))
        self.assertEqual(2, len(matrix[0]))
        self.assertEqual(2, len(matrix[1]))
        [cell_a, cell_b], [cell_c, cell_d] = matrix
        self.assertEqual(0, cell_a.x_top_left)
        self.assertEqual(0, cell_a.y_top_left)
        self.assertEqual(5, cell_a.x_bottom_right)
        self.assertEqual(2, cell_a.y_bottom_right)

        self.assertEqual(5, cell_b.x_top_left)
        self.assertEqual(0, cell_b.y_top_left)
        self.assertEqual(8, cell_b.x_bottom_right)
        self.assertEqual(2, cell_b.y_bottom_right)

        self.assertEqual(0, cell_c.x_top_left)
        self.assertEqual(2, cell_c.y_top_left)
        self.assertEqual(5, cell_c.x_bottom_right)
        self.assertEqual(5, cell_c.y_bottom_right)

        self.assertEqual(5, cell_d.x_top_left)
        self.assertEqual(2, cell_d.y_top_left)
        self.assertEqual(8, cell_d.x_bottom_right)
        self.assertEqual(5, cell_d.y_bottom_right)

    def test_no_split(self) -> None:
        cells = [[Cell(x_top_left=160, y_top_left=321, x_bottom_right=825, y_bottom_right=369),
                 Cell(x_top_left=825, y_top_left=321, x_bottom_right=1494, y_bottom_right=369)],
                 [Cell(x_top_left=160, y_top_left=374, x_bottom_right=825, y_bottom_right=423),
                 Cell(x_top_left=825, y_top_left=374, x_bottom_right=1494, y_bottom_right=423)]]
        splitted = self.splitter.split(cells=cells)
        self.assertEqual(2, len(splitted))
        self.assertEqual(2, len(splitted[0]))
        self.assertEqual(2, len(splitted[1]))
