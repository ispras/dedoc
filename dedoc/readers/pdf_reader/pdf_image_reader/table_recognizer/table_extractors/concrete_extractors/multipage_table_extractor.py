import copy
import logging
from typing import Dict, List, Tuple

from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.base_table_extractor import BaseTableExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.table_attribute_extractor import TableHeaderExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.utils import equal_with_eps


class MultiPageTableExtractor(BaseTableExtractor):

    def __init__(self, *, config: dict, logger: logging.Logger) -> None:
        super().__init__(config=config, logger=logger)
        self.single_tables = [[]]  # simple tables on all pages

    def extract_multipage_tables(self, single_tables: List[ScanTable], lines_with_meta: List[LineWithMeta]) -> List[ScanTable]:
        if len(single_tables) == 0 or len(single_tables) == 1:
            return single_tables

        self.single_tables = single_tables
        multipages_tables = []
        table_pages = list(map(lambda t: t.location.page_number, single_tables))
        max_page_with_table = max(table_pages, default=0)
        min_page_with_table = min(table_pages, default=max_page_with_table)

        # 1. get tables per page
        # pages distribution (page 0)
        page2tables = {
            cur_page: [t for t in self.single_tables if t.location.page_number == cur_page]
            for cur_page in range(min_page_with_table, max_page_with_table + 1)
        }

        total_cur_page = min_page_with_table
        if max_page_with_table == 0:  # check on unnecessary this block
            return single_tables

        while total_cur_page < max_page_with_table + 1:
            begin_page = total_cur_page

            # if tables are not found on the current page
            if len(page2tables[begin_page]) == 0:
                total_cur_page += 1
                continue

            # table merging analysis. Get the last table of the page. It is the first part of possible multipage table
            t1 = page2tables[begin_page][-1]

            # next pages cycle
            cur_page = begin_page + 1
            cur_page, multipage_table = self.__handle_multipage_table(cur_page, lines_with_meta, page2tables, t1, max_page_with_table)
            total_cur_page = cur_page + 1

            multipages_tables.extend(page2tables[begin_page][:-1])  # added all single tables, except the last one (multipage_table)
            multipages_tables.append(multipage_table)  # t1 became a multipages table
            page2tables[begin_page] = []

        return multipages_tables

    def __handle_multipage_table(self,
                                 cur_page: int,
                                 lines_with_meta: List[LineWithMeta],
                                 page2tables: Dict,
                                 t1: ScanTable,
                                 max_page_with_tables: int) -> Tuple[int, ScanTable]:
        while True:
            if cur_page == max_page_with_tables + 1:  # end of the document
                return cur_page, t1

            if len(page2tables[cur_page]) == 0:  # tables are not found on the current page
                return cur_page, t1

            # the first table on the current page
            t2 = page2tables[cur_page][0]
            if self.config.get("debug_mode", False):
                self.logger.debug(f"cur page: {cur_page}")

            # t2 is continuation of t1
            if self.__is_one_table(t1, t2):
                # t2 is merged with t1
                t1.extended(t2)
                page2tables[cur_page].pop(0)
                self.__delete_ref_table(lines=lines_with_meta, table_name=t2.uid)
            else:
                if len(page2tables[cur_page]) > 0:
                    cur_page -= 1  # analysis from the current page, not the next one
                return cur_page, t1

            # if there are several tables on the current page, end of parsing of the current multipage table
            if len(page2tables[cur_page]) > 0:
                cur_page -= 1  # analysis from the current page, not the next one
                return cur_page, t1

            cur_page += 1

    def __delete_ref_table(self, lines: List[LineWithMeta], table_name: str) -> None:
        for line in lines:
            for num, ann in enumerate(line.annotations):
                if isinstance(ann, TableAnnotation) and ann.value == table_name:
                    line.annotations.pop(num)
                    return

    @staticmethod
    def __get_width_cell_wo_separating(row: List[Cell]) -> List[int]:
        widths = []
        prev_cell_uuid = None
        cell_x_left = None
        cell_x_right = None
        for column_num, cell in enumerate(row):
            if prev_cell_uuid is None:  # the first column
                cell_x_left = cell.bbox.x_top_left
                cell_x_right = cell.bbox.x_bottom_right
                prev_cell_uuid = cell.uuid
                continue

            if prev_cell_uuid != cell.uuid:  # a new cell starts
                widths.append(cell_x_right - cell_x_left)
                cell_x_left = cell.bbox.x_top_left

            cell_x_right = cell.bbox.x_bottom_right

            if column_num == len(row) - 1:  # the last column
                widths.append(cell_x_right - cell_x_left)

        return widths

    def __is_equal_width_cells(self, table_part_1: List[List[Cell]], table_part_2: List[List[Cell]]) -> bool:
        width_cell1 = self.__get_width_cell_wo_separating(table_part_1[-1])
        width_cell2 = self.__get_width_cell_wo_separating(table_part_2[0])

        for i in range(0, len(width_cell1)):
            eps = max(4, int(width_cell1[i] * 0.1))  # error +-1% from the width
            if len(width_cell2) <= i or (not equal_with_eps(width_cell1[i], width_cell2[i], eps)):
                if self.config.get("debug_mode", False):
                    self.logger.debug(f"1 - {width_cell1[i]}")
                    self.logger.debug(f"2 - {width_cell2[i]}")
                    self.logger.debug(f"eps = {eps}")
                return False

        return True

    def __is_one_table(self, t1: ScanTable, t2: ScanTable) -> bool:
        # condition 1. Width1 == Width2. Tables widths should be equal
        width1 = abs(t1.locations[-1].bbox.width)
        width2 = abs(t2.locations[0].bbox.width)
        eps_width = int(width1 * 0.03)  # error +-1% from width
        if not equal_with_eps(width1, width2, eps_width):
            if self.config.get("debug_mode", False):
                self.logger.debug("Different width tables")
                self.logger.debug(f"w1, w2, eps = {width1}, {width2}, {eps_width}")
            return False

        # condition 2. Exclusion of the duplicated header (if any)
        attr1 = TableHeaderExtractor.get_header_table(t1.cells)
        attr2 = TableHeaderExtractor.get_header_table(t2.cells)
        t2_update = copy.deepcopy(t2)
        if TableHeaderExtractor.is_equal_header(attr1, attr2):
            t2_update.cells = t2_update.cells[len(attr2):]

        if len(t2_update.cells) == 0 or len(t1.cells) == 0:
            return False

        TableHeaderExtractor.clear_attributes(t2_update.cells)

        # condition 3. Number of columns should be equal
        if len(t1.cells[-1]) != len(t2_update.cells[0]):
            if self.config.get("debug_mode", False):
                self.logger.debug("Different count column")
            return False

        # condition 4. Comparison of the widths of last and first rows
        if t1.check_on_cell_instance() and t2_update.check_on_cell_instance() and not self.__is_equal_width_cells(t1.cells, t2_update.cells):
            if self.config.get("debug_mode", False):
                self.logger.debug("Different width columns")
            return False

        # condition 5. Check table layout
        t1_relative_bb = t1.locations[-1].to_relative_bbox_dict()
        t2_relative_bb = t2.locations[0].to_relative_bbox_dict()
        if t1_relative_bb and t2_relative_bb:
            t1_bottom = t1_relative_bb["y_top_left"] + t1_relative_bb["height"]  # the end of the table should be at the end of the page
            t2_top = t2_relative_bb["y_top_left"]                                # the beginning of the table should be in the beginning of the page
            if t1_bottom < 0.7 or t2_top > 0.3:
                return False

        t2.cells = copy.deepcopy(t2_update.cells)  # save changes
        return True
