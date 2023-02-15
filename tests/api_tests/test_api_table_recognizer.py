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
        table = res['content']['tables'][0]
        self._check_similarity(table['cells'][0][1], "Наименование участкового лестничества")
        self._check_similarity(table['cells'][2][1], "Итого")
        self._check_similarity(table['cells'][13][0], "Выращивание лесных, плодовых, ягодных, "
                                                      "декоративных растений, лекарственных растений")
        self._check_similarity(table['cells'][13][3], "1272100,0")

    def test_api_table_recognition_4(self) -> None:
        file_name = "example_with_table17.jpg"
        table = self._send_request(file_name)['content']['tables'][0]
        self._check_similarity(table['cells'][0][1], "Наименование\nучасткового\nлестничества")
        self._check_similarity(table['cells'][0][2], 'Неречень кварталов или их частей')
        self._check_similarity(table['cells'][3][3], '801 976,3')

    def test_api_table_recognition_horizontal_union_1(self) -> None:
        file_name = 'example_with_table_horizontal_union.jpg'
        table = self._send_request(file_name)['content']['tables'][0]

        self._check_similarity(table['cells'][0][1], "Наименование позиции")
        self._check_similarity(table['cells'][1][1], "Наименование позиции")
        self._check_similarity(table['cells'][0][2], "Начальная (максимальная) цена за единицу\nпродукции")
        self._check_similarity(table['cells'][1][2], "рублей, включая НДС\n(20%)")
        self._check_similarity(table['cells'][0][3], "Начальная (максимальная) цена за единицу\nпродукции")
        self._check_similarity(table['cells'][1][3], "рублей, без учета НДС\n(20%)")

    def test_api_table_recognition_hor_and_vert_union_2(self) -> None:
        file_name = "example_with_table_hor_vert_union.png"
        table = self._send_request(file_name, data={"language": "rus"})['content']['tables'][0]

        self._check_similarity(table['cells'][0][6], "Стоимость единицы, руб.")
        self._check_similarity(table['cells'][1][6], "В Tоm числе")
        self._check_similarity(table['cells'][2][6], "Осн.З/п")

        self._check_similarity(table['cells'][0][10], "Общая стоимость, руб.")
        self._check_similarity(table['cells'][1][10], "Всего")
        self._check_similarity(table['cells'][2][10], "Всего")

        self._check_similarity(table['cells'][0][12], "Общая стоимость, руб.")
        self._check_similarity(table['cells'][1][12], "В том числе")
        self._check_similarity(table['cells'][2][12], "Эк.Маш")

    def _check_header_table(self, cells: List[List[str]]) -> None:
        self._check_similarity(cells[0][0], "№\nп/п", threshold=0.5)
        self._check_similarity(cells[0][1], "№\nпункта", threshold=0.01)
        self._check_similarity(cells[0][2], "Содержание по каждому пункту")
        self._check_similarity(cells[0][3], "Установка и эксплуатация")
        self._check_similarity(cells[0][4], "По разделам о\n"
                                            "применимости\n"
                                            "оборудования в целях\n"
                                            "разделения рабочего труда\n"
                                            "работников. Разделение\n"
                                            "оборудования по зонам\n"
                                            "ответственности\n"
                                            "работников и отражение на\n"
                                            "производительности труда")
        self._check_similarity(cells[0][5], "По территорийальному\n"
                                            "разделенияю  условий\n"
                                            "труда работников,\n"
                                            "отражение на\n"
                                            "продолжительности\n"
                                            "рабочего дня и\n"
                                            "дополнтельных выплат")
        self._check_similarity(cells[0][6], "По образовательной или\n"
                                            "научной организации")
        self._check_similarity(cells[0][7], "По БДНЗ и ОПРМ")
        self._check_similarity(cells[0][8], "По филиалу ОПИМ")
        self._check_similarity(cells[0][9], "Систетематический\nконтроль")
        self._check_similarity(cells[0][10], "Экспертная оценка")

    @unittest.skip("TODO")
    def test_api_table_recognition_with_diff_orient_cells_90(self) -> None:
        file_name = "example_table_with_90_orient_cells.pdf"
        response = self._send_request(file_name, dict(orient_analysis_cells=True, orient_cell_angle="90"))
        table = response['content']['tables'][0]

        self._check_header_table(table['cells'])

    @unittest.skip
    def test_api_table_recognition_with_diff_orient_cells_270(self) -> None:
        file_name = "example_table_with_270_orient_cells.pdf"
        response = self._send_request(file_name, dict(orient_analysis_cells=True, orient_cell_angle="270"))
        table = response['content']['tables'][0]
        self._check_header_table(table['cells'])

    def test_pdf_table(self) -> None:
        file_name = "example_with_table1.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]

        rows = table["cells"]

        self.assertEqual("№", rows[0][0])
        self.assertEqual("Компания", rows[0][1])
        self.assertEqual("Адрес", rows[0][2])
        self.assertEqual("Контакты", rows[0][3])

        self.assertEqual("1", rows[1][0])
        self.assertEqual('ООО "Айтехникс"', rows[1][1])
        self.assertEqual("Емельяновский район, МО\nСолонцовский сельсовет, площадка\nЗападная, 2a cr3",
                         rows[1][2])
        self.assertEqual("Наталья Медведева\n8-908-215-75-05", rows[1][3])

        self.assertEqual("6", rows[6][0])
        self.assertEqual('ООО "Скай-\nтехнолоджи"', rows[6][1])
        self.assertEqual('Пр. Свободный 75', rows[6][2])
        self.assertEqual("Андрей Горбунов\n8-913-560-50-09", rows[6][3])

    def test_rectangular(self) -> None:
        file_name = "rectangular.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]
        cells = table["cells"]
        self.assertListEqual(['Фамилия', 'Имя', 'Отчество'], cells[0])
        self.assertListEqual(['Иванов', 'Иван', 'Иванович'], cells[1])
        self.assertListEqual(['Петров', 'Пётр', 'Петрович'], cells[2])

    def test_merged_vertical(self) -> None:
        file_name = "merged_vertical.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]
        cells = table["cells"]

        self.assertListEqual(['Фамилия\nИванов\nПетров', 'Имя', 'Отчество'], cells[0])
        self.assertListEqual(['Фамилия\nИванов\nПетров', 'Иван', 'Иванович'], cells[1])
        self.assertListEqual(['Фамилия\nИванов\nПетров', 'Пётр', 'Петрович'], cells[2])

    def test_merged_horizontal(self) -> None:
        file_name = "merged_horizontal.pdf"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]
        cells = table["cells"]

        self.assertListEqual(['Фамилия Имя Отчество', 'Фамилия Имя Отчество', 'Фамилия Имя Отчество'], cells[0])
        self.assertListEqual(['Иванов', 'Иван', 'Иванович'], cells[1])
        self.assertListEqual(['Петров', 'Пётр', 'Петрович'], cells[2])

    @unittest.skip("unskip when pdf_with_text_layer=true work")
    def test_tables_annotations(self) -> None:
        file_name = "two_column_document.pdf"
        result = self._send_request(file_name, data={"pdf_with_text_layer": "true"})
        content = result["content"]
        tree = content["structure"]
        tables = content["tables"]
        self.assertEqual(3, len(tables))
        self._check_tree_sanity(tree)
        lines = tree2linear(tree)
        expected_lines = ["Sections 1 through 9 of this document.",
                          "additions",
                          "line"
                          ]
        for line in lines:
            annotations = [a for a in line["annotations"] if a["name"] == "table"]
            for annotation in annotations:
                start = annotation["start"]
                end = annotation["end"]
                self.assertIn(line["text"][start: end].strip(), expected_lines)

    @unittest.skip("unskip when pdf_with_text_layer=true work")
    def test_false_table(self) -> None:
        file_name = "пример.pdf"
        result = self._send_request(file_name, data={"pdf_with_text_layer": "auto"})
        tree = result["content"]["structure"]
        tables = result["content"]["tables"]
        self._check_tree_sanity(tree)
        self.assertEqual(0, len(tables))
        text = self._get_by_tree_path(tree, "0.0")["text"].strip()
        self.assertEqual("Сегодня мы сравним рост разных человеков.", text)

    @unittest.skip("unskip when pdf_with_text_layer=true work")
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
