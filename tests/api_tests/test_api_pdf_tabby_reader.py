import os
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfTabbyReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_with_text_layer", file_name)

    def __filter_by_name(self, annotations: List[dict], name: str) -> List[dict]:
        return [annotation for annotation in annotations if annotation["name"] == name]

    def test_example_file(self) -> None:
        file_name = "english_doc.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        self.check_english_doc(result)

    def test_article(self) -> None:
        file_name = "../pdf_auto/0004057v1.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        content = result["content"]
        tree = content["structure"]
        self._check_tree_sanity(tree)
        node = self._get_by_tree_path(tree, "0.0")
        self.assertIn("UWB@FinTOC-2019 Shared Task: Financial Document Title Detection", node["text"])

    def test_presentation(self) -> None:
        file_name = "line_classifier.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        content = result["content"]
        tables = content["tables"]
        self.assertEqual(0, len(tables))

        tree = content["structure"]
        self._check_tree_sanity(tree)
        node = self._get_by_tree_path(tree, "0")
        self.assertEqual("root", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("Docreader система разметки\nИль", node["text"].strip()[:30])

    def test_pdf_with_text_style(self) -> None:
        file_name = "diff_styles.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="tabby"))

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree=tree)
        sub1 = self._get_by_tree_path(tree, "0.0.0")
        self.assertEqual('1.1 TimesNewRomanItalicBold20\n', sub1["text"])
        self.assertIn({'start': 0, 'end': 29, "name": "size", 'value': '20'}, sub1['annotations'])

        sub1sub1 = self._get_by_tree_path(tree, "0.0.0.0")
        self.assertEqual('Different styles(Arial16):\n', sub1sub1['text'])
        self.assertIn({'start': 0, 'end': 26, "name": "size", 'value': '15'}, sub1sub1['annotations'])

        sub2 = self._get_by_tree_path(tree, "0.1.0")
        self.assertEqual('1. TimesNewRoman18\n', sub2['text'])
        self.assertIn({'start': 0, 'end': 2, "name": "size", 'value': '15'}, sub2['annotations'])

        sub3 = self._get_by_tree_path(tree, "0.1.1")
        self.assertEqual('2. TimesNewRoman9, TimesNewRomanBold7.5, TimesNewRoman6.5\n', sub3['text'])
        self.assertIn({'start': 3, 'end': 18, "name": "size", 'value': '9'}, sub3['annotations'])

        sub4 = self._get_by_tree_path(tree, "0.1.2")
        self.assertEqual('3. TimesNewRomanItalic14, Calibri18, Tahoma16\n', sub4['text'])
        self.assertIn({'start': 3, 'end': 25, "name": "size", 'value': '14'}, sub4['annotations'])

    def test_tables2(self) -> None:
        file_name = "VVP_global_table.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="tabby"))

        content = result["content"]
        tables = content["tables"]
        self.assertEqual(1, len(tables))

        table = tables[0]["cells"]
        self.assertEqual("Государство", table[0][0])
        self.assertEqual("Место", table[0][1])
        self.assertEqual("ВВП (по ППС) за 2018 г.", table[0][2])
        self.assertEqual("Китай", table[1][0])
        self.assertEqual("1", table[1][1])
        self.assertEqual("25362", table[1][2])
        self.assertEqual("США", table[2][0])
        self.assertEqual("2", table[2][1])
        self.assertEqual("20494", table[2][2])
        self.assertEqual("Индия", table[3][0])
        self.assertEqual("3", table[3][1])
        self.assertEqual("10498", table[3][2])
        self.assertEqual("Япония", table[4][0])
        self.assertEqual("4", table[4][1])
        self.assertEqual("5415", table[4][2])
        self.assertEqual("Германия", table[5][0])
        self.assertEqual("5", table[5][1])
        self.assertEqual("4456", table[5][2])
        self.assertEqual("Франция", table[6][0])
        self.assertEqual("9", table[6][1])
        self.assertEqual("3037", table[6][2])
        self.assertEqual("Россия", table[7][0])
        self.assertEqual("6", table[7][1])
        self.assertEqual("4051", table[7][2])
        self.assertEqual("Индонезия", table[8][0])
        self.assertEqual("7", table[8][1])
        self.assertEqual("3495", table[8][2])
        self.assertEqual("Бразилия", table[9][0])
        self.assertEqual("8", table[9][1])
        self.assertEqual("3366", table[9][2])
        self.assertEqual("Франция", table[10][0])
        self.assertEqual("9", table[10][1])
        self.assertEqual("3037", table[10][2])

        tree = content["structure"]
        self._check_tree_sanity(tree)
        node = self._get_by_tree_path(tree, "0")
        self.assertEqual("root", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

    def test_pdf_with_tables(self) -> None:
        file_name = "VVP_6_tables.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="tabby"))

        content = result["content"]
        tables = content["tables"]
        self.assertEqual(4, len(tables))

        table = tables[0]["cells"]
        self.assertEqual("Государство", table[0][0])
        self.assertEqual("Место", table[0][1])
        self.assertEqual("ВВП (по ППС) за 2018 г.", table[0][2])
        self.assertEqual("Китай", table[1][0])
        self.assertEqual("1", table[1][1])
        self.assertEqual("25362", table[1][2])
        self.assertEqual("США", table[2][0])
        self.assertEqual("2", table[2][1])
        self.assertEqual("20494", table[2][2])

        table = tables[1]["cells"]
        self.assertEqual("Государство", table[0][0])
        self.assertEqual("Место", table[0][1])
        self.assertEqual("ВВП (по ППС) за 2018 г.", table[0][2])
        self.assertEqual("Индия", table[1][0])
        self.assertEqual("3", table[1][1])
        self.assertEqual("10498", table[1][2])
        self.assertEqual("Япония", table[2][0])
        self.assertEqual("4", table[2][1])
        self.assertEqual("5415", table[2][2])
        self.assertEqual("Германия", table[3][0])
        self.assertEqual("5", table[3][1])
        self.assertEqual("4456", table[3][2])
        self.assertEqual("Франция", table[4][0])
        self.assertEqual("9", table[4][1])
        self.assertEqual("3037", table[4][2])

        table = tables[2]["cells"]
        self.assertEqual("Государство", table[0][0])
        self.assertEqual("Место", table[0][1])
        self.assertEqual("ВВП (по ППС) за 2018 г.", table[0][2])
        self.assertEqual("Россия", table[1][0])
        self.assertEqual("6", table[1][1])
        self.assertEqual("4051", table[1][2])
        self.assertEqual("Индонезия", table[2][0])
        self.assertEqual("7", table[2][1])
        self.assertEqual("3495", table[2][2])
        self.assertEqual("Бразилия", table[3][0])
        self.assertEqual("8", table[3][1])
        self.assertEqual("3366", table[3][2])
        self.assertEqual("Франция", table[4][0])
        self.assertEqual("9", table[4][1])
        self.assertEqual("3037", table[4][2])

        table = tables[3]["cells"]
        self.assertEqual("", table[0][0])
        self.assertEqual("2016", table[0][1])
        self.assertEqual("2017", table[0][2])
        self.assertEqual("2018", table[0][3])
        self.assertEqual("2019", table[0][4])
        self.assertEqual("", table[1][0])
        self.assertEqual("Прогноз", table[1][1])
        self.assertEqual("Прогноз бюджета", table[1][2])
        self.assertEqual("Прогноз бюджета", table[1][3])
        self.assertEqual("Прогноз бюджета", table[1][4])
        self.assertEqual("Расходы", table[2][0])
        self.assertEqual("19,8", table[2][1])
        self.assertEqual("18,6", table[2][2])
        self.assertEqual("17,3", table[2][3])
        self.assertEqual("16,1", table[2][4])
        self.assertEqual("Доходы", table[3][0])
        self.assertEqual("16,1", table[3][1])
        self.assertEqual("15,4", table[3][2])
        self.assertEqual("15,1", table[3][3])
        self.assertEqual("15,0", table[3][4])
        self.assertEqual("Нефтегазовые<br />доходы", table[4][0])
        self.assertEqual("5,8", table[4][1])
        self.assertEqual("5,8", table[4][2])
        self.assertEqual("5,5", table[4][3])
        self.assertEqual("5,4", table[4][4])
        self.assertEqual("Ненефтегазов<br />ые доходы", table[5][0])
        self.assertEqual("10,4", table[5][1])
        self.assertEqual("9,6", table[5][2])
        self.assertEqual("9,6", table[5][3])
        self.assertEqual("9,6", table[5][4])
        self.assertEqual("Сальдо<br />бюджета", table[6][0])
        self.assertEqual("-3,7", table[6][1])
        self.assertEqual("-3,2", table[6][2])
        self.assertEqual("-2,2", table[6][3])
        self.assertEqual("-1,2", table[6][4])
        self.assertEqual("", table[7][0])
        self.assertEqual("2016", table[7][1])
        self.assertEqual("2017", table[7][2])
        self.assertEqual("2018", table[7][3])
        self.assertEqual("2019", table[7][4])
        self.assertEqual("", table[8][0])
        self.assertEqual("Прогноз", table[8][1])
        self.assertEqual("Прогноз бюджета", table[8][2])
        self.assertEqual("Прогноз бюджета", table[8][3])
        self.assertEqual("Прогноз бюджета", table[8][4])
        self.assertEqual("Расходы", table[9][0])
        self.assertEqual("19,8", table[9][1])
        self.assertEqual("18,6", table[9][2])
        self.assertEqual("17,3", table[9][3])
        self.assertEqual("16,1", table[9][4])
        self.assertEqual("Доходы", table[10][0])
        self.assertEqual("16,1", table[10][1])
        self.assertEqual("15,4", table[10][2])
        self.assertEqual("15,1", table[10][3])
        self.assertEqual("15,0", table[10][4])
        self.assertEqual("Нефтегазовые<br />доходы", table[11][0])
        self.assertEqual("5,8", table[11][1])
        self.assertEqual("5,8", table[11][2])
        self.assertEqual("5,5", table[11][3])
        self.assertEqual("5,4", table[11][4])
        self.assertEqual("Ненефтегазов<br />ые доходы", table[12][0])
        self.assertEqual("10,4", table[12][1])
        self.assertEqual("9,6", table[12][2])
        self.assertEqual("9,6", table[12][3])
        self.assertEqual("9,6", table[12][4])
        self.assertEqual("Сальдо<br />бюджета", table[13][0])
        self.assertEqual("-3,7", table[13][1])
        self.assertEqual("-3,2", table[13][2])
        self.assertEqual("-2,2", table[13][3])
        self.assertEqual("-1,2", table[13][4])
        self.assertEqual("", table[14][0])
        self.assertEqual("2016", table[14][1])
        self.assertEqual("2017", table[14][2])
        self.assertEqual("2018", table[14][3])
        self.assertEqual("2019", table[14][4])
        self.assertEqual("", table[15][0])
        self.assertEqual("Прогноз", table[15][1])
        self.assertEqual("Прогноз бюджета", table[15][2])
        self.assertEqual("Прогноз бюджета", table[15][3])
        self.assertEqual("Прогноз бюджета", table[15][4])
        self.assertEqual("Расходы", table[16][0])
        self.assertEqual("19,8", table[16][1])
        self.assertEqual("18,6", table[16][2])
        self.assertEqual("17,3", table[16][3])
        self.assertEqual("16,1", table[16][4])
        self.assertEqual("Доходы", table[17][0])
        self.assertEqual("16,1", table[17][1])
        self.assertEqual("15,4", table[17][2])
        self.assertEqual("15,1", table[17][3])
        self.assertEqual("15,0", table[17][4])
        self.assertEqual("Нефтегазовые<br />доходы", table[18][0])
        self.assertEqual("5,8", table[18][1])
        self.assertEqual("5,8", table[18][2])
        self.assertEqual("5,5", table[18][3])
        self.assertEqual("5,4", table[18][4])
        self.assertEqual("Ненефтегазов<br />ые доходы", table[19][0])
        self.assertEqual("10,4", table[19][1])
        self.assertEqual("9,6", table[19][2])
        self.assertEqual("9,6", table[19][3])
        self.assertEqual("9,6", table[19][4])
        self.assertEqual("Сальдо<br />бюджета", table[20][0])
        self.assertEqual("-3,7", table[20][1])
        self.assertEqual("-3,2", table[20][2])
        self.assertEqual("-2,2", table[20][3])
        self.assertEqual("-1,2", table[20][4])

        tree = content["structure"]
        self._check_tree_sanity(tree)
        node = self._get_by_tree_path(tree, "0")
        self.assertEqual("root", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("ВВП\n", node["text"])
