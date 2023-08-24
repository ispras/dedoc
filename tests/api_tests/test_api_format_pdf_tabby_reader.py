import os
import unittest
from typing import List

from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.confidence_annotation import ConfidenceAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfTabbyReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_with_text_layer", file_name)

    def __filter_by_name(self, annotations: List[dict], name: str) -> List[dict]:
        return [annotation for annotation in annotations if annotation["name"] == name]

    def test_example_file(self) -> None:
        file_name = "english_doc.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        self._check_english_doc(result)

    @unittest.skip("TODO: add two layers output order support, e.g footnotes and main text.")
    def test_former_txt_file(self) -> None:
        file_name = "cp1251.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        content = result["content"]
        tree = content["structure"]
        self._check_tree_sanity(tree)
        texts = []
        for subrapagraph in tree["subparagraphs"]:
            texts.append(subrapagraph["text"])
        with open(self._get_abs_path(file_name.replace(".pdf", ".txt"))) as file:
            self.assertEqual(file.read(), "".join(texts))

    @unittest.skip("TODO: check tags extraction in this document")
    def test_article(self) -> None:
        file_name = "../pdf_auto/0004057v1.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        content = result["content"]
        tree = content["structure"]
        self._check_tree_sanity(tree)
        node = self._get_by_tree_path(tree, "0.0")
        self.assertIn("UWB@FinTOC-2019 Shared Task: Financial Document Title Detection", node["text"][0])
        node = self._get_by_tree_path(tree, "0.11")
        self.assertIn("The shared task consists of two subtasks:", node["text"])
        node = self._get_by_tree_path(tree, "0.20")
        self.assertIn("3 Dataset", node["text"])
        node = self._get_by_tree_path(tree, "0.39")
        self.assertIn("4 Issues", node["text"])

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
        self.assertIn("Docreader система разметки\nИлья Козлов", node["text"])

        node = self._get_by_tree_path(tree, "0.2")
        self.assertEqual("list", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.2.0")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("1. Общая идея систем разметки", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.2.1")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("2. Как запустить", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.2.2")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("3. Формируем задания", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.2.3")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("4. Раздаём и собираем задания", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.2.3.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("3/100", node["text"].strip()[:30])

    def test_pdf_with_text_style(self) -> None:
        file_name = "diff_styles.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="tabby"))

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree=tree)
        sub1 = self._get_by_tree_path(tree, "0.0.0")
        self.assertEqual("1.1 TimesNewRomanItalicBold20\n", sub1["text"])
        self.assertIn({"start": 0, "end": 29, "name": "size", "value": "20"}, sub1["annotations"])

        sub1sub1 = self._get_by_tree_path(tree, "0.0.0.0")
        self.assertEqual("Different styles(Arial16):\n", sub1sub1["text"])
        self.assertIn({"start": 0, "end": 26, "name": "size", "value": "15"}, sub1sub1["annotations"])

        sub2 = self._get_by_tree_path(tree, "0.1.0")
        self.assertEqual("1. TimesNewRoman18\n", sub2["text"])
        self.assertIn({"start": 3, "end": 18, "name": "size", "value": "18"}, sub2["annotations"])

        sub3 = self._get_by_tree_path(tree, "0.1.1")
        self.assertEqual("2. TimesNewRoman9, TimesNewRomanBold7.5, TimesNewRoman6.5\n", sub3["text"])
        self.assertIn({"start": 3, "end": 18, "name": "size", "value": "9"}, sub3["annotations"])
        self.assertIn({"start": 19, "end": 57, "name": "size", "value": "6"}, sub3["annotations"])

        sub4 = self._get_by_tree_path(tree, "0.1.2")
        self.assertEqual("3. TimesNewRomanItalic14, Calibri18, Tahoma16\n", sub4["text"])
        self.assertIn({"start": 3, "end": 25, "name": "size", "value": "14"}, sub4["annotations"])
        self.assertIn({"start": 26, "end": 36, "name": "size", "value": "18"}, sub4["annotations"])

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
        result = self._send_request(file_name, dict(pdf_with_text_layer="tabby", document_orientation="no_change"))

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
        self.assertEqual("Ненефтегазов\nые доходы", table[19][0])
        self.assertEqual("10,4", table[19][1])
        self.assertEqual("9,6", table[19][2])
        self.assertEqual("9,6", table[19][3])
        self.assertEqual("9,6", table[19][4])
        self.assertEqual("Сальдо\nбюджета", table[20][0])
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
        self.assertEqual("ВВП", node["text"].strip())

        node = self._get_by_tree_path(tree, "0.1")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("ВВП (валовой внутренний продук", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.4.0")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("1. В соответствии с доходами.", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.4.1")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("2. В соответствии с расходами.", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.4.2")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("3. В соответствии с полученной", node["text"].strip()[:30])
