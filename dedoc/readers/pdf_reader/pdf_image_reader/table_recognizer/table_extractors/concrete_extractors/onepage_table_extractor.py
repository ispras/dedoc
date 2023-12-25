import copy
import logging
import uuid
from typing import List

import numpy as np

from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.data_classes.tables.table_tree import TableTree
from dedoc.readers.pdf_reader.data_classes.tables.table_type import TableTypeAdditionalOptions
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.cell_splitter import CellSplitter
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.split_last_hor_union_cells import split_last_column
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.base_table_extractor import BaseTableExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.table_attribute_extractor import TableAttributeExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.img_processing import detect_tables_by_contours


class OnePageTableExtractor(BaseTableExtractor):

    def __init__(self, *, config: dict, logger: logging.Logger) -> None:
        super().__init__(config=config, logger=logger)

        self.image = None
        self.page_number = 0
        self.attribute_selector = TableAttributeExtractor(logger=self.logger)
        self.count_vertical_extended = 0
        self.splitter = CellSplitter()
        self.table_options = TableTypeAdditionalOptions()
        self.language = "rus"

    def extract_onepage_tables_from_image(self,
                                          image: np.ndarray,
                                          page_number: int,
                                          language: str,
                                          orient_analysis_cells: bool,
                                          orient_cell_angle: int,  # TODO remove
                                          table_type: str) -> List[ScanTable]:
        """
        extracts tables from input image
        :param image: input gray image
        :param page_number:
        :param language: language for Tesseract
        :param orient_analysis_cells: need or not analyse orientations of cells
        :param orient_cell_angle: angle of cells (needs if orient_analysis_cells==True)
        :return: List[ScanTable]
        """
        self.image = image
        self.page_number = page_number
        self.language = language

        # Read the image
        tables_tree, contours, angle_rotate = detect_tables_by_contours(image,
                                                                        language=language,
                                                                        config=self.config,
                                                                        orient_analysis_cells=orient_analysis_cells,
                                                                        table_type=table_type)

        tables = self.__build_structure_table_from_tree(tables_tree=tables_tree, table_type=table_type)

        for matrix in tables:
            for location in matrix.locations:
                location.bbox.rotate_coordinates(angle_rotate=-angle_rotate, image_shape=image.shape)
                location.rotated_angle = angle_rotate

        tables = self.__select_attributes_matrix_tables(tables=tables)

        return tables

    """ TODO fix in the future (REMOVE)
    def __detect_diff_orient(self, cell_text: str) -> bool:
        # 1 - разбиваем на строки длины которых состоят хотя бы из одного символа
        parts = cell_text.split("\n")
        parts = [p for p in parts if len(p) > 0]

        # 2 - подсчитываем среднюю длину строк ячейки
        len_parts = [len(p) for p in parts]
        avg_len_part = np.average(len_parts)

        # Эвристика: считаем что ячейка повернута, если у нас большое количество строк и строки короткие
        if len(parts) > TableTree.minimal_cell_cnt_line \
                and avg_len_part < TableTree.minimal_cell_avg_length_line:
            return True
        return False

    def __correct_orient_cell(self, cell: Cell, language: str, rotated_angle: int) -> [Cell, np.ndarray]:
        img_cell = self.image[cell.y_top_left: cell.y_bottom_right, cell.x_top_left: cell.x_bottom_right]
        rotated_image_cell = rotate_image(img_cell, -rotated_angle)

        output_dict = get_text_with_bbox_from_cells(img_cell, language=language)
        line_boxes = [
            TextWithBBox(text=line.text, page_num=page_num, bbox=line.bbox, line_num=line_num, annotations=line.get_annotations(width, height))
            for line_num, line in enumerate(output_dict.lines)]
        # get_cell_text_by_ocr(rotated_image_cell, language=language)
        cell.set_rotated_angle(rotated_angle=-rotated_angle)
        return cell, rotated_image_cell


    def __analyze_header_cell_with_diff_orient(self, tables: List[ScanTable], language: str,
                                               rotated_angle: int) -> List[ScanTable]:

        for table in tables:
            attrs = TableAttributeExtractor.get_header_table(table.matrix_cells)
            for i, row in enumerate(attrs):
                for j, attr in enumerate(row):
                    if self.__detect_diff_orient(attr.text):
                        rotated_cell, rotated_image = self.__correct_orient_cell(attr, language=language, rotated_angle=rotated_angle)
                        table.matrix_cells[i][j] = rotated_cell

        return tables
    """

    def __select_attributes_matrix_tables(self, tables: List[ScanTable]) -> List[ScanTable]:
        for matrix in tables:
            matrix = self.attribute_selector.select_attributes(matrix)

            if self.config.get("debug_mode", False):
                self._print_table_attr(matrix.matrix_cells)

        return tables

    def __get_matrix_table_from_tree(self, table_tree: TableTree) -> ScanTable:
        """
        Function builds matrix table from sorted cells of the tree table
        :param table_tree: tree of cells
        """
        matrix = []
        line = []
        for cell in table_tree.children:
            if len(line) != 0 and abs(cell.cell_box.y_top_left - line[-1].y_top_left) > 15:  # add eps
                cpy_line = copy.deepcopy(line)
                matrix.append(cpy_line)
                line.clear()

            cell_ = Cell(x_top_left=cell.cell_box.x_top_left,
                         x_bottom_right=cell.cell_box.x_bottom_right,
                         y_top_left=cell.cell_box.y_top_left,
                         y_bottom_right=cell.cell_box.y_bottom_right,
                         id_con=cell.id_contours,
                         lines=cell.lines,
                         contour_coord=cell.cell_box)
            line.append(cell_)
        matrix.append(line)

        # sorting column in each row
        for i in range(0, len(matrix)):
            matrix[i] = sorted(matrix[i], key=lambda cell: cell.x_top_left, reverse=False)

        matrix_table = ScanTable(matrix_cells=matrix, bbox=table_tree.cell_box, page_number=self.page_number, name=str(uuid.uuid4()))

        return matrix_table

    def __build_structure_table_from_tree(self, tables_tree: TableTree, table_type: str) -> List[ScanTable]:
        """
        Parsing all tables that exist in the tables_tree
        """
        tables = []
        for table_tree in tables_tree.children:
            try:
                cur_table = self.__get_matrix_table_from_tree(table_tree)
                # Эвристика 1: Таблица должна состоять из 1 строк и более
                if len(cur_table.matrix_cells) > 0:
                    cur_table.matrix_cells = self.splitter.split(cells=cur_table.matrix_cells)

                    # Эвристика 2: таблица должна иметь больше одного столбца
                    if len(cur_table.matrix_cells[0]) > 1 or (self.table_options.detect_one_cell_table in table_type and cur_table.matrix_cells[0] != []):
                        tables.append(cur_table)

                    if self.table_options.split_last_column in table_type:
                        cur_table.matrix_cells = split_last_column(cur_table.matrix_cells, language=self.language, image=self.image)
            except Exception as ex:
                self.logger.warning(f"Warning: unrecognized table into page {self.page_number}. {ex}")
                if self.config.get("debug_mode", False):
                    raise ex
        return tables
