import json
import os
import unittest
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from tests.test_utils import tree2linear


class TestRecognizedTable(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "tables", file_name)

    def test_api_table_recognition_3(self) -> None:
        file_name = "example_with_table16.jpg"
        res = self._send_request(file_name)
        table = res["content"]["tables"][0]["cells"]
        self._check_similarity(self._get_text_of_row(table[0])[1], "Наименование\nучасткового\nлестничества")
        self._check_similarity(self._get_text_of_row(table[2])[1], "Итого")
        self._check_similarity(self._get_text_of_row(table[13])[0],
                               "Выращивание лесных, плодовых, ягодных, декоративных растений, лекарственных растений")
        self._check_similarity(self._get_text_of_row(table[13])[3], "1272100,0")

    def test_api_table_recognition_4(self) -> None:
        file_name = "example_with_table17.jpg"
        table = self._send_request(file_name)["content"]["tables"][0]["cells"]
        self._check_similarity(self._get_text_of_row(table[0])[1], "Наименование\nучасткового\nлестничества")
        self._check_similarity(self._get_text_of_row(table[0])[2], "Неречень кварталов или их частей")
        self._check_similarity(self._get_text_of_row(table[3])[3], "801 976,3")

    def test_api_table_recognition_horizontal_union_1(self) -> None:
        file_name = "example_with_table_horizontal_union.jpg"
        table = self._send_request(file_name)["content"]["tables"][0]["cells"]

        row0 = self._get_text_of_row(table[0])
        row1 = self._get_text_of_row(table[1])

        self._check_similarity(row0[1], "Наименование позиции")
        self._check_similarity(row1[1], "Наименование позиции")
        self._check_similarity(row0[2], "Начальная (максимальная) цена за единицу\nпродукции")
        self._check_similarity(row1[2], "рублей, включая НДС\n(20%)")
        self._check_similarity(row0[3], "Начальная (максимальная) цена за единицу\nпродукции")
        self._check_similarity(row1[3], "рублей, без учета НДС\n(20%)")

    def test_api_table_recognition_hor_and_vert_union_2(self) -> None:
        file_name = "example_with_table_hor_vert_union.png"
        table = self._send_request(file_name, data={"language": "rus"})["content"]["tables"][0]["cells"]

        row0 = self._get_text_of_row(table[0])
        row1 = self._get_text_of_row(table[1])
        row2 = self._get_text_of_row(table[2])

        self._check_similarity(row0[6], "Стоимость единицы, руб.")
        self._check_similarity(row1[6], "В Tоm числе")
        self._check_similarity(row2[6], "Осн.З/п")

        self._check_similarity(row0[10], "Общая стоимость, руб.")
        self._check_similarity(row1[10], "Всего")
        self._check_similarity(row2[10], "Всего")

        self._check_similarity(row0[12], "Общая стоимость, руб.")
        self._check_similarity(row1[12], "В том числе")
        self._check_similarity(row2[12], "Эк.Маш")

    def _check_header_table(self, cells: List[dict]) -> None:
        row0 = self._get_text_of_row(cells[0])
        self._check_similarity(row0[0], "№\nп/п", threshold=0.5)
        self._check_similarity(row0[1], "№\nпункта", threshold=0.01)
        self._check_similarity(row0[2], "Содержание по каждому пункту")
        self._check_similarity(row0[3], "Установка и эксплуатация")
        self._check_similarity(row0[4], "По разделам о\n"
                                        "применимости\n"
                                        "оборудования в целях\n"
                                        "разделения рабочего труда\n"
                                        "работников. Разделение\n"
                                        "оборудования по зонам\n"
                                        "ответственности\n"
                                        "работников и отражение на\n"
                                        "производительности труда")
        self._check_similarity(row0[5], "По территорийальному\n"
                                        "разделенияю  условий\n"
                                        "труда работников,\n"
                                        "отражение на\n"
                                        "продолжительности\n"
                                        "рабочего дня и\n"
                                        "дополнтельных выплат")
        self._check_similarity(row0[6], "По образовательной или\n"
                                        "научной организации")
        self._check_similarity(row0[7], "По БДНЗ и ОПРМ")
        self._check_similarity(row0[8], "По филиалу ОПИМ")
        self._check_similarity(row0[9], "Систетематический\nконтроль")
        self._check_similarity(row0[10], "Экспертная оценка")

    @unittest.skip("TODO")
    def test_api_table_recognition_with_diff_orient_cells_90(self) -> None:
        file_name = "example_table_with_90_orient_cells.pdf"
        response = self._send_request(file_name, dict(orient_analysis_cells=True, orient_cell_angle="90"))
        table = response["content"]["tables"][0]

        self._check_header_table(table["cells"])

    @unittest.skip
    def test_api_table_recognition_with_diff_orient_cells_270(self) -> None:
        file_name = "example_table_with_270_orient_cells.pdf"
        response = self._send_request(file_name, dict(orient_analysis_cells=True, orient_cell_angle="270"))
        table = response["content"]["tables"][0]
        self._check_header_table(table["cells"])

    def test_pdf_table(self) -> None:
        file_name = "example_with_table1.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]["cells"]
        row0 = self._get_text_of_row(table[0])
        row1 = self._get_text_of_row(table[1])
        row6 = self._get_text_of_row(table[6])

        self.assertEqual("№", row0[0])
        self.assertEqual("Компания", row0[1])
        self.assertEqual("Адрес", row0[2])
        self.assertEqual("Контакты", row0[3])

        self.assertEqual("1", row1[0])
        self.assertEqual('ООО "Айтехникс"', row1[1])
        self.assertEqual("Емельяновский район, МО\nСолонцовский сельсовет, площадка\nЗападная, 2a cr3", row1[2])
        self.assertEqual("Наталья Медведева\n8-908-215-75-05", row1[3])

        self.assertEqual("6", row6[0])
        self.assertEqual('ООО "Скай-\nтехнолоджи"', row6[1])
        self.assertEqual("Пр. Свободный 75", row6[2])
        self.assertEqual("Андрей Горбунов\n8-913-560-50-09", row6[3])

    def test_rectangular(self) -> None:
        file_name = "rectangular.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]["cells"]
        row0 = self._get_text_of_row(table[0])
        row1 = self._get_text_of_row(table[1])
        row2 = self._get_text_of_row(table[2])

        self.assertListEqual(["Фамилия", "Имя", "Отчество"], row0)
        self.assertListEqual(["Иванов", "Иван", "Иванович"], row1)
        self.assertListEqual(["Петров", "Пётр", "Петрович"], row2)

    def test_merged_vertical(self) -> None:
        file_name = "merged_vertical.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]["cells"]
        row0 = self._get_text_of_row(table[0])
        row1 = self._get_text_of_row(table[1])
        row2 = self._get_text_of_row(table[2])

        self.assertListEqual(["Фамилия\nИванов\nПетров", "Имя", "Отчество"], row0)
        self.assertListEqual(["Фамилия\nИванов\nПетров", "Иван", "Иванович"], row1)
        self.assertListEqual(["Фамилия\nИванов\nПетров", "Пётр", "Петрович"], row2)

    def test_merged_horizontal(self) -> None:
        file_name = "merged_horizontal.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]["cells"]
        row0 = self._get_text_of_row(table[0])
        row1 = self._get_text_of_row(table[1])
        row2 = self._get_text_of_row(table[2])

        self.assertListEqual(["Фамилия Имя Отчество", "Фамилия Имя Отчество", "Фамилия Имя Отчество"], row0)
        self.assertListEqual(["Иванов", "Иван", "Иванович"], row1)
        self.assertListEqual(["Петров", "Пётр", "Петрович"], row2)

    def test_tables_annotations(self) -> None:
        file_name = "two_column_document.pdf"
        result = self._send_request(file_name, data={"pdf_with_text_layer": "true"})
        content = result["content"]
        tree = content["structure"]
        tables = content["tables"]
        self.assertEqual(3, len(tables))
        self._check_tree_sanity(tree)
        lines = tree2linear(tree)
        expected_lines = ["Sections 1 through 9 of this document.", "additions", "line"]
        for line in lines:
            annotations = [a for a in line["annotations"] if a["name"] == "table"]
            for annotation in annotations:
                start = annotation["start"]
                end = annotation["end"]
                self.assertIn(line["text"][start: end].strip(), expected_lines)

    def test_false_table(self) -> None:
        file_name = "пример.pdf"
        result = self._send_request(file_name, data={"pdf_with_text_layer": "auto"})
        tree = result["content"]["structure"]
        tables = result["content"]["tables"]
        self._check_tree_sanity(tree)
        self.assertEqual(0, len(tables))
        text = self._get_by_tree_path(tree, "0.0")["text"].strip()
        self.assertEqual("Сегодня мы сравним рост разных человеков.", text)

    def test_false_table2(self) -> None:
        file_name = "not_table.pdf"
        result = self._send_request(file_name, data={"pdf_with_text_layer": "true"})
        tree = result["content"]["structure"]
        tables = result["content"]["tables"]
        self._check_tree_sanity(tree)
        self.assertEqual(0, len(tables))

    def test_detect_small_table(self) -> None:
        file_name = "invoice.jpg"
        result = self._send_request(file_name, data={"language": "rus"})
        tables = result["content"]["tables"]
        self.assertEqual(2, len(tables))

    def _test_bbox_annotations(self, node: dict, target_dict: dict) -> None:
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "bounding box"]
        annotations_dict = json.loads(annotations[0]["value"])
        for key in target_dict:
            self.assertAlmostEqual(float(annotations_dict[key]), target_dict[key], None, None, delta=0.05)

    def test_multipage_gost_table(self) -> None:
        file_name = "gost_multipage_table.pdf"
        result = self._send_request(file_name, data={"need_gost_frame_analysis": "True"})  # don't pass pdf_with_text_layer to check condition in PDFBaseReader
        self.assertTrue(len(result["content"]["tables"][0]["cells"]) > 35)
        target_bbox_dict = {
            "x_top_left": 0.14,
            "y_top_left": 0.11,
            "width": 0.07,
            "height": 0.01,
            "page_width": 1653,
            "page_height": 2339
        }
        self._test_bbox_annotations(result["content"]["structure"]["subparagraphs"][0], target_bbox_dict)
        self.assertTrue("Состав квалификационных испытаний" in result["content"]["structure"]["subparagraphs"][0]["text"])
        self.assertTrue("KR13" in result["content"]["tables"][0]["cells"][-1][0]["lines"][0]["text"])  # check the last row of multipage table
        target_bbox_dict_1 = {
            "x_top_left": 0.15,
            "y_top_left": 0.58,
            "width": 0.04,
            "height": 0.009,
            "page_width": 1653,
            "page_height": 2339
        }
        self._test_bbox_annotations(result["content"]["tables"][0]["cells"][-1][0]["lines"][0], target_bbox_dict_1)
        self.assertTrue("R13.1" in result["content"]["tables"][0]["cells"][-1][1]["lines"][0]["text"])  # check that it belongs to first and only table
        self.assertTrue("Испытание по проверке" in result["content"]["tables"][0]["cells"][-1][2]["lines"][0]["text"])
        self.assertTrue("3.6" in result["content"]["tables"][0]["cells"][-1][3]["lines"][0]["text"])
        self.assertTrue("7.4.9" in result["content"]["tables"][0]["cells"][-1][4]["lines"][0]["text"])

    def test_multipage_gost_table_with_text_layer(self) -> None:
        file_name = "gost_multipage_table_2.pdf"
        result = self._send_request(file_name, data={"need_gost_frame_analysis": "True", "pdf_with_text_layer": "True"})
        self.__check_content(result)

    def test_multipage_gost_table_tabby(self) -> None:
        file_name = "gost_multipage_table_2.pdf"
        result = self._send_request(file_name, data={"need_gost_frame_analysis": "True", "pdf_with_text_layer": "tabby"})
        self.__check_content(result)

    def __check_content(self, result: dict) -> None:
        self.assertEqual(len(result["content"]["tables"][0]["cells"]), 14)
        target_bbox_dict = {
            "x_top_left": 0.12,
            "y_top_left": 0.56,
            "width": 0.01,
            "height": 0.01,
            "page_width": 595,
            "page_height": 841
        }
        self._test_bbox_annotations(result["content"]["structure"]["subparagraphs"][0]["subparagraphs"][0], target_bbox_dict)
        self.assertTrue("Sample text 1" in result["content"]["structure"]["subparagraphs"][0]["subparagraphs"][0]["text"])
        self.assertTrue("SAMPLE TEXT" in result["content"]["tables"][0]["cells"][0][0]["lines"][0]["text"])
        target_bbox_dict_1 = {
            "x_top_left": 0.13,
            "y_top_left": 0.61,
            "width": 0.06,
            "height": 0.007,
            "page_width": 595,
            "page_height": 841
        }
        self._test_bbox_annotations(result["content"]["tables"][0]["cells"][0][0]["lines"][0], target_bbox_dict_1)
        self.assertTrue("2" in result["content"]["tables"][0]["cells"][-1][0]["lines"][0]["text"])
        self.assertEqual(len(result["content"]["tables"]), 1)

    def test_multipage_gost_table_with_text_layer_and_pages_param(self) -> None:
        file_name = "gost_multipage_table_2.pdf"
        result = self._send_request(file_name, data={"need_gost_frame_analysis": "True", "pdf_with_text_layer": "True", "pages": "2:"})
        self.assertEqual(len(result["content"]["tables"]), 1)
        self.assertEqual(len(result["content"]["tables"][0]["cells"]), 5)
        self.assertTrue("SAMPLE TEXT" in result["content"]["tables"][0]["cells"][0][0]["lines"][0]["text"])
        target_bbox_dict_1 = {
            "x_top_left": 0.13,
            "y_top_left": 0.07,
            "width": 0.06,
            "height": 0.007,
            "page_width": 595,
            "page_height": 841
        }
        self._test_bbox_annotations(result["content"]["tables"][0]["cells"][0][0]["lines"][0], target_bbox_dict_1)
        self.assertTrue("2" in result["content"]["tables"][0]["cells"][-1][0]["lines"][0]["text"])
        target_bbox_dict_2 = {
            "x_top_left": 0.13,
            "y_top_left": 0.15,
            "width": 0.005,
            "height": 0.007,
            "page_width": 595,
            "page_height": 841
        }
        self._test_bbox_annotations(result["content"]["tables"][0]["cells"][-1][0]["lines"][0], target_bbox_dict_2)
