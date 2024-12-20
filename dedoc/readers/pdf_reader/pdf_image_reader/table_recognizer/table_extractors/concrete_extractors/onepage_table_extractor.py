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

        self.image = None
        self.page_number = 0
        self.table_header_extractor = TableHeaderExtractor(logger=self.logger)
        self.count_vertical_extended = 0
        self.splitter = CellSplitter()
        self.table_options = TableTypeAdditionalOptions()
        self.language = "rus"

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
        tables = self.__build_structure_table_from_tree(tables_tree=tables_tree, table_type=table_type)

        for table in tables:
            for location in table.locations:
                location.bbox.rotate_coordinates(angle_rotate=-angle_rotate, image_shape=image.shape)
                location.rotated_angle = angle_rotate

        return tables

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

        matrix_table = ScanTable(cells=matrix, bbox=table_tree.cell_box, page_number=self.page_number)

        return matrix_table

    def __build_structure_table_from_tree(self, tables_tree: TableTree, table_type: str) -> List[ScanTable]:
        """
        Parsing all tables that exist in the tables_tree
        """
        tables = []
        for table_tree in tables_tree.children:
            try:
                table = self.__get_matrix_table_from_tree(table_tree)
                table.cells = self.handle_cells(table.cells, table_type)
                tables.append(table)
            except Exception as ex:
                self.logger.warning(f"Warning: unrecognized table into page {self.page_number}. {ex}")
                if self.config.get("debug_mode", False):
                    raise ex
        return tables

    def handle_cells(self, cells: List[List[Cell]], table_type: str = "") -> List[List[Cell]]:
        # Эвристика 1: Таблица должна состоять из 1 строк и более
        if len(cells) < 1:
            raise RecognizeError("Invalid recognized table")

        cells = self.splitter.split(cells=cells)

        # Эвристика 2: таблица должна иметь больше одного столбца
        if cells[0] == [] or (len(cells[0]) <= 1 and self.table_options.detect_one_cell_table not in table_type):
            raise RecognizeError("Invalid recognized table")

        # Postprocess table
        if self.table_options.split_last_column in table_type:
            cells = split_last_column(cells, language=self.language, image=self.image)

        self.table_header_extractor.set_header_cells(cells)

        if self.config.get("debug_mode", False):
            self._print_table_attr(cells)

        return cells
