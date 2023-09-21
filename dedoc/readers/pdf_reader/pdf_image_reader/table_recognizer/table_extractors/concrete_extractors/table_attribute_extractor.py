import logging
from typing import List

from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.utils import similarity


class TableAttributeExtractor(object):
    """
    Class finds and labels "is_attributes=True" attribute cells into ScanTable
    """

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def select_attributes(self, scan_table: ScanTable) -> ScanTable:
        return self.__set_attributes_for_type_top(scan_table)

    @staticmethod
    def is_equal_attributes(attr1: List[List[Cell]], attr2: List[List[Cell]], thr_similarity: int = 0.8) -> bool:
        if len(attr1) != len(attr2):
            return False

        for i in range(len(attr1)):
            if len(attr1[i]) != len(attr2[i]):
                return False
            for j in range(len(attr1[i])):
                if similarity(attr1[i][j].get_text(), attr2[i][j].get_text()) < thr_similarity:
                    return False

        return True

    @staticmethod
    def get_header_table(matrix_table: List[List[Cell]]) -> List[List[Cell]]:
        header_rows = len(matrix_table)
        for (i, row) in enumerate(matrix_table):
            attrs = [cell for cell in row if cell.is_attribute]
            if len(attrs) != len(row):
                header_rows = i
                break

        return matrix_table[:header_rows]

    @staticmethod
    def clear_attributes(matrix_table: List[List[Cell]]) -> None:
        for row in matrix_table:
            for cell in row:
                cell.is_attribute = False
                cell.is_attribute_required = False

    def __is_indexable_column(self, matrix_table: List[List[Cell]], column_id: int, max_raw_of_search: int) -> bool:
        # № п/п
        for i in range(0, max_raw_of_search + 1):
            if column_id < len(matrix_table[i]) and "№" in matrix_table[i][column_id].get_text() and len(
                    matrix_table[i][column_id].get_text()) < len("№ п/п\n"):
                return True
        return False

    def __set_attributes_for_type_top(self, scan_table: ScanTable) -> ScanTable:
        vertical_union_columns = self.__analyze_attr_for_vertical_union_columns(scan_table)
        horizontal_union_rows = self.__analyze_attr_for_horizontal_union_raws(scan_table)

        # simple table
        if (0 not in horizontal_union_rows) and len(vertical_union_columns) == 0:
            self.__analyze_attr_for_simple_table(scan_table)

        return scan_table

    def __is_empty_column(self, matrix_table: List[List[Cell]], column_id: int) -> bool:
        all_empty = True
        for i in range(0, len(matrix_table)):
            if len(matrix_table[i]) <= column_id:
                break
            if matrix_table[i][column_id].get_text() != "":
                all_empty = False
                break
        return all_empty

    def __is_empty_row(self, matrix_table: List[List[Cell]], row_index: int) -> bool:
        all_empty = True
        for j in range(0, len(matrix_table[row_index])):
            if matrix_table[row_index][j].get_text() != "":
                all_empty = False
                break
        return all_empty

    def __analyze_attr_for_vertical_union_columns(self, scan_table: ScanTable) -> List[int]:
        vertical_union_columns = []
        if len(vertical_union_columns) != 0 and len(scan_table.matrix_cells) > 1:
            self.logger.debug("ATTR_TYPE: vertical union table")
            row_max_attr = 1
            i = 1

            # Установка атрибутов таблицы
            for i in range(0, row_max_attr):
                for j in range(0, len(scan_table.matrix_cells[i])):
                    scan_table.matrix_cells[i][j].is_attribute = True
            # Установка обязательных атрибутов
            scan_table.matrix_cells[0][0].is_attribute_required = True
            for j in range(1, len(scan_table.matrix_cells[0])):
                is_attribute_required = True
                if is_attribute_required:
                    scan_table.matrix_cells[0][j].is_attribute_required = True

        return vertical_union_columns

    def __analyze_attr_for_horizontal_union_raws(self, scan_table: ScanTable) -> List[int]:
        horizontal_union_rows = []
        union_first = False

        for i in range(0, len(scan_table.matrix_cells)):
            if len(horizontal_union_rows) > 0 and i not in horizontal_union_rows:
                horizontal_union_rows.append(i)
                if not self.__is_empty_row(scan_table.matrix_cells, i):
                    break

        if union_first and len(horizontal_union_rows) != 0:
            self.logger.debug("ATTR_TYPE: horizontal_union_rows")
            for i in range(0, len(horizontal_union_rows)):
                for j in range(0, len(scan_table.matrix_cells[i])):
                    scan_table.matrix_cells[i][j].is_attribute = True
            scan_table.matrix_cells[0][0].is_attribute_required = True
            first_required_column = 0
            # search indexable_column
            # один один столбец должен быть (0) - нумерованным,
            # один (1) - с обязательными поляями, один (2) - с необязательными
            # поэтому len(matrix_table) > first_required_column + 2
            if len(horizontal_union_rows) > 0 and \
                    self.__is_indexable_column(scan_table.matrix_cells, first_required_column, max_raw_of_search=horizontal_union_rows[-1]) \
                    and len(scan_table.matrix_cells) > first_required_column + 2:
                scan_table.matrix_cells[0][first_required_column + 1].is_attribute_required = True

            # Полностью пустые строки не могут быть атрибутами (не информативны)
            # Перенос атрибутов на след строку таблицы
            index_empty_rows = horizontal_union_rows[-1]
            if self.__is_empty_row(scan_table.matrix_cells, index_empty_rows) and len(scan_table.matrix_cells) != index_empty_rows + 1:
                horizontal_union_rows.append(index_empty_rows + 1)
                for j in range(0, len(scan_table.matrix_cells[index_empty_rows + 1])):
                    scan_table.matrix_cells[index_empty_rows + 1][j].is_attribute = True
                self.logger.debug("detect empty attributes row")
        return horizontal_union_rows

    def __analyze_attr_for_simple_table(self, scan_table: ScanTable) -> None:
        self.logger.debug("ATTR_TYPE: simple table")
        for j in range(0, len(scan_table.matrix_cells[0])):
            scan_table.matrix_cells[0][j].is_attribute = True
        # set first required column
        j = 0
        first_required_column = j
        while j < len(scan_table.matrix_cells[0]):
            if not self.__is_empty_column(scan_table.matrix_cells, j):
                scan_table.matrix_cells[0][j].is_attribute_required = True
                first_required_column = j
                break
            j += 1
        # search indexable_column
        # один один столбец должен быть (0) - нумерованным,
        # один (1) - с обязательными поляями, один (2) - с необязательными
        # поэтому len(matrix_table) > first_required_column + 2
        if self.__is_indexable_column(scan_table.matrix_cells, first_required_column, 0) and len(scan_table.matrix_cells) > first_required_column + 2:
            scan_table.matrix_cells[0][first_required_column + 1].is_attribute_required = True
