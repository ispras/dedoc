import copy
import logging
from typing import List

import numpy as np

from dedoc.common.exceptions.recognize_error import RecognizeError
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
from dedoc.readers.pdf_reader.data_classes.tables.table_type import TableTypeAdditionalOptions
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.cell_splitter import CellSplitter
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.split_last_hor_union_cells import split_last_column
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.base_table_extractor import BaseTableExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.table_attribute_extractor import TableHeaderExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.img_processing import detect_tables_by_contours


class OnePageTableExtractor(BaseTableExtractor):

    def __init__(self, *, config: dict, logger: logging.Logger) -> None:
        super().__init__(config=config, logger=logger)

        self.language = "rus"
        self.page_number = None
        self.image = None
        self.table_header_extractor = TableHeaderExtractor(logger=self.logger)
        self.count_vertical_extended = 0
        self.splitter = CellSplitter()
        self.table_options = TableTypeAdditionalOptions()

    def extract_onepage_tables_from_image(self, image: np.ndarray, page_number: int, language: str, table_type: str) -> List[ScanTable]:
        """
        extracts tables from input image
        :param image: input gray image
        :param page_number:
        :param language: language for Tesseract
        :return: List[ScanTable]
        """
        self.image = image
        self.page_number = page_number
        self.language = language

        # Read the image
        tables_tree, contours, angle_rotate = detect_tables_by_contours(image, language=language, config=self.config, table_type=table_type)
        return [table for _, table in self.build_tables_from_tree(image, page_number, tables_tree, angle_rotate, table_type)]

    def build_tables_from_tree(self, image: np.ndarray, page_number: int, tables_tree: TableTree, angle_rotate: float, table_type: str) -> List[tuple]:
        """Build ScanTables from an already-detected tree (cells may carry text or not yet), returning
        ``(source_subtree, ScanTable)`` pairs with locations rotated back to the input orientation. Source tracking
        lets the staged pipeline prune the tree to the tables that survive filtering, then rebuild them with cell text
        after the GPU cell OCR. ``image`` is used for its shape only (page dims + rotation)."""
        self.image = image
        self.page_number = page_number
        pairs = []
        for table_tree in tables_tree.children:
            try:
                table = self.__get_matrix_table_from_tree(table_tree)
                table.cells = self.handle_cells(table.cells, table_type)
            except Exception as ex:
                if self.config.get("debug_mode", False):
                    self.logger.warning(f"Warning: unrecognized table into page {self.page_number}. {ex}")
                continue
            for location in table.locations:
                location.bbox.rotate_coordinates(angle_rotate=-angle_rotate, image_shape=image.shape)
                location.rotated_angle = angle_rotate
            pairs.append((table_tree, table))
        return pairs

    def __get_matrix_table_from_tree(self, table_tree: TableTree) -> ScanTable:
        """
        Function builds matrix table from sorted cells of the tree table
        :param table_tree: tree of cells
        """
        matrix = []
        line = []
        for cell in table_tree.children:
            if len(line) != 0 and abs(cell.cell_box.y_top_left - line[-1].bbox.y_top_left) > 15:  # add eps
                cpy_line = copy.deepcopy(line)
                matrix.append(cpy_line)
                line.clear()

            cell_ = Cell(bbox=cell.cell_box, id_con=cell.id_contours, lines=cell.lines, contour_coord=cell.cell_box)
            line.append(cell_)
        matrix.append(line)

        # sorting column in each row
        for i, row in enumerate(matrix):
            matrix[i] = sorted(row, key=lambda cell: cell.bbox.x_top_left, reverse=False)

        page_height, page_width = self.image.shape[:2]
        matrix_table = ScanTable(cells=matrix, bbox=table_tree.cell_box, page_number=self.page_number, page_width=page_width, page_height=page_height)

        return matrix_table

    def handle_cells(self, cells: List[List[Cell]], table_type: str = "") -> List[List[Cell]]:
        # Heuristic 1: The table must have 1 or more rows.
        if len(cells) < 1:
            raise RecognizeError("Invalid recognized table. Heuristic 1: The table must have 1 or more rows.")

        cells = self.splitter.split(cells=cells)

        # Heuristic 2: The table must have more than one column.
        if cells[0] == [] or (len(cells[0]) <= 1 and self.table_options.detect_one_cell_table not in table_type):
            raise RecognizeError("Invalid recognized table. Heuristic 2: The table must have more than one column.")

        # Postprocess table
        if self.table_options.split_last_column in table_type:
            cells = split_last_column(cells, language=self.language, image=self.image)

        self.table_header_extractor.set_header_cells(cells)

        if self.config.get("debug_mode", False):
            self._print_table_attr(cells)

        return cells
