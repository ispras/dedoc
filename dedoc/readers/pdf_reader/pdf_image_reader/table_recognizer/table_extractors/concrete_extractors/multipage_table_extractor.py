from typing import List
import logging

from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.tables.cell import Cell
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.base_table_extractor import BaseTableExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_extractors.concrete_extractors.table_attribute_extractor import TableAttributeExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.utils import equal_with_eps


class MultiPageTableExtractor(BaseTableExtractor):

    def __init__(self, *, config: dict, logger: logging.Logger) -> None:
        super().__init__(config=config, logger=logger)
        self.single_tables = [[]]  # simple tables on all pages

    def extract_multipage_tables(self,
                                 single_tables: List[ScanTable],
                                 lines_with_meta: List[LineWithMeta]) -> List[ScanTable]:
        self.single_tables = single_tables
        multipages_tables = []
        list_page_with_tables = []
        total_pages = max((table.page_number + 1 for table in single_tables), default=0)
        for cur_page in range(total_pages):
            # 1. get possible diaposon of neighbors pages with tables
            # распределение по страницам
            list_mp_table = [t for t in self.single_tables if t.page_number == cur_page]
            list_page_with_tables.append(list_mp_table)

        # проход по всем таблицам. Основной цикл обработки.
        total_cur_page = 0
        if total_pages == 1:
            for tbls in list_page_with_tables:
                multipages_tables.extend(tbls)
            return multipages_tables

        while total_cur_page < total_pages:
            begin_page = total_cur_page

            # если нет таблиц на текущей странице
            if len(list_page_with_tables[begin_page]) == 0:
                total_cur_page += 1
                continue

            # последняя таблица на текущей странице может иметь продолжение
            # начинаем анализ на слияние таблиц
            t1 = list_page_with_tables[begin_page][-1]

            # цикл по следующим страницам
            finish = False  # условие выхода анализа текущей многостраничной таблицы
            cur_page = begin_page + 1

            while not finish:
                # условия выхода
                if cur_page == total_pages:  # достигнут конец документа
                    finish = True
                    continue

                if len(list_page_with_tables[cur_page]) == 0:  # нет таблиц на текущей странице
                    finish = True
                    continue

                # рассматриваем первую страницу на текущей странице
                t2 = list_page_with_tables[cur_page][0]
                if self.config.get("debug_mode", False):
                    self.logger.debug("cur page: {}".format(cur_page))

                # проверка что t2 является продолжением t1
                if self.__is_one_table(t1, t2):
                    # таблица присоединяется к первой
                    t1.extended(t2)
                    list_page_with_tables[cur_page].pop(0)
                    self.__delete_ref_table(lines=lines_with_meta, table_name=t2.name)
                else:
                    if len(list_page_with_tables[cur_page]) > 0:
                        cur_page -= 1  # чтобы начать с этой страницы анализ, а не со следующей
                    finish = True
                    continue

                if not finish:
                    # если несколько таблиц на странице, то завершаем объединение многостраничной таблицы
                    if len(list_page_with_tables[cur_page]) > 0:
                        cur_page -= 1  # чтобы начать с этой страницы анализ, а не со следующей
                        finish = True
                    else:  # продолжаем обход
                        cur_page += 1

            total_cur_page = cur_page + 1  # анализ следующей страницы

            multipages_tables.extend(list_page_with_tables[begin_page][:-1])
            multipages_tables.append(t1)  # добавление многостраничной таблицы
            list_page_with_tables[begin_page] = []
            for page in range(begin_page + 1, min(cur_page + 1, total_pages)):
                if len(list_page_with_tables[page]) > 0:
                    multipages_tables.extend(list_page_with_tables[page])
                    list_page_with_tables[page] = []

        return multipages_tables

    def __delete_ref_table(self, lines: List[LineWithMeta], table_name: str) -> None:
        for line in lines:
            for num, ann in enumerate(line.annotations):
                if isinstance(ann, TableAnnotation) and ann.value == table_name:
                    line.annotations.pop(num)
                    return

    @staticmethod
    def __get_width_cell_wo_separating(row: List[Cell]) -> List[int]:
        widths = []
        prev_uid = None
        start = None
        end = None
        for cell_id, cell in enumerate(row):
            if prev_uid is None:
                start = cell.x_top_left
                prev_uid = cell.cell_uid
            elif prev_uid != cell.cell_uid:
                widths.append(end - start)
                start = cell.x_top_left
            end = cell.x_bottom_right
            if cell_id == len(row) - 1:
                widths.append(end - start)
        return widths

    def __is_equal_width_cells(self, table_part_1: List[List[Cell]], table_part_2: List[List[Cell]]) -> bool:
        width_cell1 = self.__get_width_cell_wo_separating(table_part_1[-1])
        width_cell2 = self.__get_width_cell_wo_separating(table_part_2[0])

        for i in range(0, len(width_cell1)):
            eps = max(4, int(width_cell1[i] * 0.1))  # +-1% от ширины погрешность
            if len(width_cell2) <= i or (not equal_with_eps(width_cell1[i], width_cell2[i], eps)):
                if self.config.get("debug_mode", False):
                    self.logger.debug("1 - {}".format(width_cell1[i]))
                    self.logger.debug("2 - {}".format(width_cell2[i]))
                    self.logger.debug("eps = {}".format(eps))
                return False

        return True

    def __is_one_table(self, t1: ScanTable, t2: ScanTable) -> bool:
        # condition 1. Width1 == Width2. Ширина таблиц должна совпадать
        width1 = abs(t1.locations[-1].bbox.width)
        width2 = abs(t2.locations[0].bbox.width)
        eps_width = int(width1 * 0.03)  # в диапозоне +-1% от ширины погрешность
        if not equal_with_eps(width1, width2, eps_width):
            if self.config.get("debug_mode", False):
                self.logger.debug("Different width tables")
                self.logger.debug("w1, w2, eps = {}, {}, {}".format(width1, width2, eps_width))
            return False

        # condition 2. исключение дублированного заголовка (если он есть)
        attr1 = TableAttributeExtractor.get_header_table(t1.matrix_cells)
        attr2 = TableAttributeExtractor.get_header_table(t2.matrix_cells)
        if TableAttributeExtractor.is_equal_attributes(attr1, attr2):
            t2.matrix_cells = t2.matrix_cells[len(attr2):]

        if len(t2.matrix_cells) == 0 or len(t1.matrix_cells) == 0:
            return False

        # очищаем признак аттрибутов у второй части таблицы
        TableAttributeExtractor.clear_attributes(t2.matrix_cells)

        # condition 3. количество столбцов должно совпадать
        if len(t1.matrix_cells[-1]) != len(t2.matrix_cells[0]):
            if self.config.get("debug_mode", False):
                self.logger.debug("Different count column")
            return False

        # condition 4. сравнение ширин столбцов последнего и первого рядов
        if not self.__is_equal_width_cells(t1.matrix_cells, t2.matrix_cells):
            if self.config.get("debug_mode", False):
                self.logger.debug("Different width columns")
            return False

        return True
