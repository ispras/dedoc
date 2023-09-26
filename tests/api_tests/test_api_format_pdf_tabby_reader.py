import os
import unittest
from typing import List

from dedoc.data_structures.concrete_annotations.bbox_annotation import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
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

        self.assertListEqual(["Государство", "Место", "ВВП (по ППС) за 2018 г."], self._get_text_of_row(table[0]))
        self.assertListEqual(["Китай", "1", "25362"], self._get_text_of_row(table[1]))
        self.assertListEqual(["США", "2", "20494"], self._get_text_of_row(table[2]))
        self.assertListEqual(["Индия", "3", "10498"], self._get_text_of_row(table[3]))
        self.assertListEqual(["Япония", "4", "5415"], self._get_text_of_row(table[4]))
        self.assertListEqual(["Германия", "5", "4456"], self._get_text_of_row(table[5]))
        self.assertListEqual(["Франция", "9", "3037"], self._get_text_of_row(table[6]))
        self.assertListEqual(["Россия", "6", "4051"], self._get_text_of_row(table[7]))
        self.assertListEqual(["Индонезия", "7", "3495"], self._get_text_of_row(table[8]))
        self.assertListEqual(["Бразилия", "8", "3366"], self._get_text_of_row(table[9]))
        self.assertListEqual(["Франция", "9", "3037"], self._get_text_of_row(table[10]))

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
        self.assertListEqual(["Государство", "Место", "ВВП (по ППС) за 2018 г."], self._get_text_of_row(table[0]))
        self.assertListEqual(["Китай", "1", "25362"], self._get_text_of_row(table[1]))
        self.assertListEqual(["США", "2", "20494"], self._get_text_of_row(table[2]))

        table = tables[1]["cells"]
        self.assertListEqual(["Государство", "Место", "ВВП (по ППС) за 2018 г."], self._get_text_of_row(table[0]))
        self.assertListEqual(["Индия", "3", "10498"], self._get_text_of_row(table[1]))
        self.assertListEqual(["Япония", "4", "5415"], self._get_text_of_row(table[2]))
        self.assertListEqual(["Германия", "5", "4456"], self._get_text_of_row(table[3]))
        self.assertListEqual(["Франция", "9", "3037"], self._get_text_of_row(table[4]))

        table = tables[2]["cells"]
        self.assertListEqual(["Государство", "Место", "ВВП (по ППС) за 2018 г."], self._get_text_of_row(table[0]))
        self.assertListEqual(["Россия", "6", "4051"], self._get_text_of_row(table[1]))
        self.assertListEqual(["Индонезия", "7", "3495"], self._get_text_of_row(table[2]))
        self.assertListEqual(["Бразилия", "8", "3366"], self._get_text_of_row(table[3]))
        self.assertListEqual(["Франция", "9", "3037"], self._get_text_of_row(table[4]))

        table = tables[3]["cells"]
        self.assertListEqual(["", "2016", "2017", "2018", "2019"], self._get_text_of_row(table[0]))
        self.assertListEqual(["", "Прогноз", "Прогноз бюджета", "Прогноз бюджета", "Прогноз бюджета"], self._get_text_of_row(table[1]))
        self.assertListEqual(["Ненефтегазов\nые доходы", "10,4", "9,6", "9,6", "9,6"], self._get_text_of_row(table[19]))
        self.assertListEqual(["Сальдо\nбюджета", "-3,7", "-3,2", "-2,2", "-1,2"], self._get_text_of_row(table[20]))

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

    def test_pdf_annotations(self) -> None:
        file_name = "Document635.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        content = result["content"]["structure"]["subparagraphs"]
        annotations = content[0]["annotations"]
        annotation_names = {annotation["name"] for annotation in annotations}
        self.assertIn(BoldAnnotation.name, annotation_names)
        self.assertIn(SpacingAnnotation.name, annotation_names)
        self.assertIn(BBoxAnnotation.name, annotation_names)

    def test_tables_with_merged_cells(self) -> None:
        file_name = "big_table_with_merged_cells.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="tabby"))
        table = result["content"]["tables"][0]["cells"]

        hidden_cells_big_table_with_colspan = [[(1, 0), 10], [(5, 5), 5]]

        for (i, j), k in hidden_cells_big_table_with_colspan:
            self.assertFalse(table[i][j]["invisible"])
            self.assertEqual(table[i][j]["rowspan"], 1)
            self.assertEqual(table[i][j]["colspan"], k)

        self.assertFalse(table[3][0]["invisible"])
        self.assertEqual(table[3][0]["rowspan"], 3)
        self.assertEqual(table[3][0]["colspan"], 4)
