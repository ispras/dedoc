import logging
from typing import List

from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell


class BaseTableExtractor(object):
    def __init__(self, *, config: dict, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def _print_matrix_table(self, matrix_table: List[List[Cell]]) -> None:
        string = ""
        for i in range(len(matrix_table)):
            string += " ".join([str(cell.id_con) for cell in matrix_table[i]])
            string += "\n"
        self.logger.debug(f"{string}\nend table")

    def _print_table_attr(self, matrix_cells: List[List[Cell]]) -> None:
        string = "Table:\n"
        for i in range(0, len(matrix_cells)):
            string += "\t".join([f"{cell.id_con}/{cell.is_attribute}/{cell.is_attribute_required}" for cell in matrix_cells[i]])
            string += "\n"
        self.logger.debug(string)
