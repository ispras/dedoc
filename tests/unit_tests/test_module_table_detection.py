import os.path
import unittest
from typing import List

import cv2
import numpy as np

from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.accuracy_table_rec import get_quantitative_parameters
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_utils.utils import equal_with_eps, similarity as utils_similarity
from tests.test_utils import get_full_path, get_test_config


def similarity(s1: str, s2: str, threshold: float = 0.8) -> bool:
    return True if utils_similarity(s1, s2) > threshold else False


class TestRecognizedTable(unittest.TestCase):

    table_recognizer = TableRecognizer(config=get_test_config())

    def get_table(self, image: np.ndarray, language: str = "rus", table_type: str = "") -> List[ScanTable]:
        image, tables = self.table_recognizer.recognize_tables_from_image(image=image, page_number=0, language=language, table_type=table_type)
        return tables

    def test_table_wo_external_bounds(self) -> None:
        path_image = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "lising", "platezhka.jpg"))

        image = cv2.imread(path_image, 0)

        tables = self.get_table(image, "rus+eng", table_type="table_wo_external_bounds")
        bbox = tables[0].locations[0].bbox

        # LEFT-TOP point
        self.assertTrue(equal_with_eps(bbox.x_top_left, 99, 10))
        self.assertTrue(equal_with_eps(bbox.y_top_left, 279, 10))
        # WIDTH-HEIGHT table
        self.assertTrue(equal_with_eps(bbox.width, 1122, 10))
        self.assertTrue(equal_with_eps(bbox.height, 754, 10))

    def test_table_split_right_column(self) -> None:
        path_image = get_full_path("data/lising/platezhka.jpg")

        image = cv2.imread(path_image, 0)

        tables = self.get_table(image, "rus+eng", table_type="split_last_column+wo_external_bounds")
        self.assertTrue(tables[0].cells[4][-1].get_text(), "40703978900000345077")
        self.assertTrue(tables[0].cells[5][-1].get_text(), "049401814")
        self.assertTrue(tables[0].cells[6][-1].get_text(), "30101810200000000814")
        self.assertTrue(tables[0].cells[7][-1].get_text(), "049401814")
        self.assertTrue(tables[0].cells[8][-1].get_text(), "30101810200000000814")
        self.assertTrue(tables[0].cells[9][-1].get_text(), "30110978700000070815")
        self.assertTrue(tables[0].cells[10][-1].get_text(), "30110978700000070815")

    def test_table_extract_one_cell_and_one_cell_tables(self) -> None:
        path_image = get_full_path("data/lising/platezhka.jpg")
        image = cv2.imread(path_image, 0)

        tables = self.get_table(image, "rus+eng", table_type="table_wo_external_bounds+one_cell_table")

        self.assertEqual(len(tables), 4)

    def test_table_detection_1(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table3.png"), 0)
        tables = self.get_table(image)
        bbox = tables[0].locations[0].bbox

        # LEFT-TOP point
        self.assertTrue(equal_with_eps(bbox.x_top_left, 57, 10))
        self.assertTrue(equal_with_eps(bbox.y_top_left, 177, 10))
        # WIDTH-HEIGHT table
        self.assertTrue(equal_with_eps(bbox.width, 519, 10))
        self.assertTrue(equal_with_eps(bbox.height, 617, 10))

    def test_table_detection_2(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table4.jpg"), 0)
        tables = self.get_table(image)
        bbox = tables[0].locations[0].bbox
        # LEFT-TOP point
        self.assertTrue(equal_with_eps(bbox.x_top_left, 108, 30))
        self.assertTrue(equal_with_eps(bbox.y_top_left, 1525, 30))
        # WIDTH-HEIGHT table
        self.assertTrue(equal_with_eps(bbox.width, 2282, 30))
        self.assertTrue(equal_with_eps(bbox.height, 1797, 30))

    def test_table_detection_3(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table5.png"), 0)
        tables = self.get_table(image)
        bbox = tables[0].locations[0].bbox
        # LEFT-TOP point
        self.assertTrue(equal_with_eps(bbox.x_top_left, 164, 30))
        self.assertTrue(equal_with_eps(bbox.y_top_left, 261, 30))
        # WIDTH-HEIGHT table
        self.assertTrue(equal_with_eps(bbox.width, 1464, 50))
        self.assertTrue(equal_with_eps(bbox.height, 1868, 30))

    def test_table_detection_with_rotate_4(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table6.png"), 0)
        tables = self.get_table(image)
        bbox = tables[0].locations[0].bbox
        # LEFT-TOP point
        self.assertTrue(equal_with_eps(bbox.x_top_left, 57, 30))
        self.assertTrue(equal_with_eps(bbox.y_top_left, 507, 30))
        # WIDTH-HEIGHT table
        self.assertTrue(equal_with_eps(bbox.width, 1652, 30))
        self.assertTrue(equal_with_eps(bbox.height, 631, 30))

    def test_table_recognition_1(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table3.png"), 0)
        tables = self.get_table(image)

        cnt_a_cell, cnt_cell, cnt_columns, cnt_rows = get_quantitative_parameters(tables[0].cells)

        self.assertEqual(cnt_rows, 8)
        self.assertEqual(cnt_columns, 3)
        self.assertEqual(cnt_a_cell, 3)
        self.assertEqual(cnt_cell, 24)
        self.assertTrue(similarity(tables[0].cells[0][1].get_text(), "Наименование данных"))
        self.assertTrue(similarity(tables[0].cells[0][2].get_text(), "Данные"))
        self.assertTrue(similarity(tables[0].cells[4][1].get_text().capitalize(), "Инн"))
        self.assertTrue(similarity(tables[0].cells[3][1].get_text(), "Руководитель (ФИО, телефон,\nфакс, электронный адрес)"))

    def test_table_recognition_2(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table4.jpg"), 0)
        tables = self.get_table(image)

        cnt_a_cell, cnt_cell, cnt_columns, cnt_rows = get_quantitative_parameters(tables[0].cells)

        self.assertEqual(cnt_rows, 5)
        self.assertEqual(cnt_columns, 3)
        self.assertEqual(cnt_a_cell, 3)
        self.assertEqual(cnt_cell, 15)
        self.assertTrue(similarity(tables[0].cells[0][1].get_text(), "Перечень основных данных и\nтребований"))
        self.assertTrue(similarity(tables[0].cells[0][2].get_text(), "Основные данные и требования"))
        self.assertTrue(similarity(tables[0].cells[3][1].get_text(), "Количество"))
        self.assertTrue(similarity(tables[0].cells[4][1].get_text(), "Технические параметры оборудования"))

    def test_table_recognition_3(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table5.png"), 0)
        tables = self.get_table(image)

        cnt_a_cell, cnt_cell, cnt_columns, cnt_rows = get_quantitative_parameters(tables[0].cells)

        self.assertEqual(cnt_rows, 13)
        self.assertEqual(cnt_columns, 3)
        self.assertEqual(cnt_a_cell, 3)
        self.assertEqual(cnt_cell, 39)
        self.assertTrue(similarity(tables[0].cells[0][1].get_text(), "Техническая характеристика"))
        self.assertTrue(similarity(tables[0].cells[0][2].get_text(), "Показатель"))
        self.assertTrue(similarity(tables[0].cells[6][1].get_text(), "Использование крана и его механизмов"))
        self.assertTrue(similarity(tables[0].cells[7][1].get_text(), "Тип привода:"))

    def test_table_recognition_4(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table5.png"), 0)
        tables = self.get_table(image)

        cnt_a_cell, cnt_cell, cnt_columns, cnt_rows = get_quantitative_parameters(tables[0].cells)

        self.assertEqual(cnt_rows, 13)
        self.assertEqual(cnt_columns, 3)
        self.assertEqual(cnt_a_cell, 3)
        self.assertEqual(cnt_cell, 39)
        self.assertTrue(similarity(tables[0].cells[0][1].get_text(), "Техническая характеристика"))
        self.assertTrue(similarity(tables[0].cells[0][2].get_text(), "Показатель"))
        self.assertTrue(similarity(tables[0].cells[6][1].get_text(), "Использование крана и его механизмов"))
        self.assertTrue(similarity(tables[0].cells[7][1].get_text(), "Тип привода:"))

    def test_table_recognition_with_rotate_5(self) -> None:
        image = cv2.imread(get_full_path("data/tables/example_with_table6.png"), 0)
        tables = self.get_table(image)

        cnt_a_cell, cnt_cell, cnt_columns, cnt_rows = get_quantitative_parameters(tables[0].cells)

        self.assertEqual(cnt_rows, 3)
        self.assertEqual(cnt_columns, 7)
        self.assertEqual(cnt_a_cell, 7)
        self.assertEqual(cnt_cell, 21)
        self.assertTrue(similarity(tables[0].cells[0][1].get_text(), "Группа"))
        self.assertTrue(similarity(tables[0].cells[0][3].get_text(), "Наименование"))
        self.assertTrue(similarity(tables[0].cells[2][2].get_text(), "Новая\nпозиция"))
        self.assertTrue(similarity(tables[0].cells[2][5].get_text(), "3 (три)\nшт."))
