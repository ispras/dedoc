import unittest

from dedocutils.data_structures import BBox

from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.cell_splitter import CellSplitter


class TestCellSplitter(unittest.TestCase):
    splitter = CellSplitter()

    def test_merge_close_borders(self) -> None:
        cells = [
            [
                Cell(BBox(x_top_left=0, y_top_left=0, width=50, height=30)),
                Cell(BBox(x_top_left=51, y_top_left=2, width=39, height=27))
            ],
            [
                Cell(BBox(x_top_left=0, y_top_left=31, width=50, height=19)),
                Cell(BBox(x_top_left=51, y_top_left=31, width=40, height=19))
            ]
        ]
        cells_merged = self.splitter._merge_close_borders(cells)
        self.assertEqual(0, cells_merged[0][0].bbox.x_top_left)
        self.assertEqual(0, cells_merged[0][0].bbox.y_top_left)
        self.assertEqual(50, cells_merged[0][0].bbox.x_bottom_right)
        self.assertEqual(29, cells_merged[0][0].bbox.y_bottom_right)

        self.assertEqual(50, cells_merged[0][1].bbox.x_top_left)
        self.assertEqual(0, cells_merged[0][1].bbox.y_top_left)
        self.assertEqual(90, cells_merged[0][1].bbox.x_bottom_right)
        self.assertEqual(29, cells_merged[0][1].bbox.y_bottom_right)

        self.assertEqual(0, cells_merged[1][0].bbox.x_top_left)
        self.assertEqual(29, cells_merged[1][0].bbox.y_top_left)
        self.assertEqual(50, cells_merged[1][0].bbox.x_bottom_right)
        self.assertEqual(50, cells_merged[1][0].bbox.y_bottom_right)

        self.assertEqual(50, cells_merged[1][1].bbox.x_top_left)
        self.assertEqual(29, cells_merged[1][1].bbox.y_top_left)
        self.assertEqual(90, cells_merged[1][1].bbox.x_bottom_right)
        self.assertEqual(50, cells_merged[1][1].bbox.y_bottom_right)

    def test_merge_close_borders_one_cell(self) -> None:
        cells = [[Cell(BBox(x_top_left=0, y_top_left=0, width=50, height=30))]]
        cells_merged = self.splitter._merge_close_borders(cells)
        self.assertEqual(0, cells_merged[0][0].bbox.x_top_left)
        self.assertEqual(0, cells_merged[0][0].bbox.y_top_left)
        self.assertEqual(50, cells_merged[0][0].bbox.x_bottom_right)
        self.assertEqual(30, cells_merged[0][0].bbox.y_bottom_right)

    def test_merge_zero_cells(self) -> None:
        cells = [[]]
        cells_merged = self.splitter._merge_close_borders(cells)
        self.assertListEqual([[]], cells_merged)

    def test_split_zero_cells(self) -> None:
        cells = [[]]
        matrix = self.splitter.split(cells=cells)
        self.assertListEqual([[]], matrix)

    def test_split_one_cell(self) -> None:
        cells = [[Cell(BBox(x_top_left=0, y_top_left=0, width=10, height=15))]]
        matrix = self.splitter.split(cells=cells)
        self.assertEqual(1, len(matrix))
        self.assertEqual(1, len(matrix[0]))
        new_cell = matrix[0][0]
        self.assertEqual(0, new_cell.bbox.x_top_left)
        self.assertEqual(0, new_cell.bbox.y_top_left)
        self.assertEqual(10, new_cell.bbox.x_bottom_right)
        self.assertEqual(15, new_cell.bbox.y_bottom_right)

    def test_horizontal_split(self) -> None:
        cells = [
            [
                Cell(BBox(x_top_left=0, y_top_left=0, width=3, height=5)),
                Cell(BBox(x_top_left=3, y_top_left=0, width=4, height=3)),
            ],
            [
                Cell(BBox(x_top_left=3, y_top_left=3, width=4, height=2)),
            ]
        ]
        matrix = self.splitter.split(cells)
        self.assertEqual(2, len(matrix))
        self.assertEqual(2, len(matrix[0]))
        self.assertEqual(2, len(matrix[1]))
        [cell_a, cell_b], [cell_c, cell_d] = matrix
        self.assertEqual(0, cell_a.bbox.x_top_left)
        self.assertEqual(0, cell_a.bbox.y_top_left)
        self.assertEqual(3, cell_a.bbox.x_bottom_right)
        self.assertEqual(3, cell_a.bbox.y_bottom_right)

        self.assertEqual(3, cell_b.bbox.x_top_left)
        self.assertEqual(0, cell_b.bbox.y_top_left)
        self.assertEqual(7, cell_b.bbox.x_bottom_right)
        self.assertEqual(3, cell_b.bbox.y_bottom_right)

        self.assertEqual(0, cell_c.bbox.x_top_left)
        self.assertEqual(3, cell_c.bbox.y_top_left)
        self.assertEqual(3, cell_c.bbox.x_bottom_right)
        self.assertEqual(5, cell_c.bbox.y_bottom_right)

        self.assertEqual(3, cell_d.bbox.x_top_left)
        self.assertEqual(3, cell_d.bbox.y_top_left)
        self.assertEqual(7, cell_d.bbox.x_bottom_right)
        self.assertEqual(5, cell_d.bbox.y_bottom_right)

    def test_vertical_split(self) -> None:
        cells = [
            [
                Cell(BBox(x_top_left=0, y_top_left=0, width=8, height=2)),
            ],
            [
                Cell(BBox(x_top_left=0, y_top_left=2, width=5, height=3)),
                Cell(BBox(x_top_left=5, y_top_left=2, width=3, height=3)),
            ]
        ]
        matrix = self.splitter.split(cells)
        self.assertEqual(2, len(matrix))
        self.assertEqual(2, len(matrix[0]))
        self.assertEqual(2, len(matrix[1]))
        [cell_a, cell_b], [cell_c, cell_d] = matrix
        self.assertEqual(0, cell_a.bbox.x_top_left)
        self.assertEqual(0, cell_a.bbox.y_top_left)
        self.assertEqual(5, cell_a.bbox.x_bottom_right)
        self.assertEqual(2, cell_a.bbox.y_bottom_right)

        self.assertEqual(5, cell_b.bbox.x_top_left)
        self.assertEqual(0, cell_b.bbox.y_top_left)
        self.assertEqual(8, cell_b.bbox.x_bottom_right)
        self.assertEqual(2, cell_b.bbox.y_bottom_right)

        self.assertEqual(0, cell_c.bbox.x_top_left)
        self.assertEqual(2, cell_c.bbox.y_top_left)
        self.assertEqual(5, cell_c.bbox.x_bottom_right)
        self.assertEqual(5, cell_c.bbox.y_bottom_right)

        self.assertEqual(5, cell_d.bbox.x_top_left)
        self.assertEqual(2, cell_d.bbox.y_top_left)
        self.assertEqual(8, cell_d.bbox.x_bottom_right)
        self.assertEqual(5, cell_d.bbox.y_bottom_right)

    def test_no_split(self) -> None:
        cells = [
            [
                Cell(BBox(x_top_left=160, y_top_left=321, width=665, height=48)),
                Cell(BBox(x_top_left=825, y_top_left=321, width=669, height=48))
            ],
            [
                Cell(BBox(x_top_left=160, y_top_left=374, width=665, height=49)),
                Cell(BBox(x_top_left=825, y_top_left=374, width=669, height=49))
            ]
        ]

        splitted = self.splitter.split(cells=cells)
        self.assertEqual(2, len(splitted))
        self.assertEqual(2, len(splitted[0]))
        self.assertEqual(2, len(splitted[1]))
