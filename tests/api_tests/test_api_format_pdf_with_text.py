import os
import unittest
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_with_text_layer", file_name)

    def __filter_by_name(self, annotations: List[dict], name: str) -> List[dict]:
        return [annotation for annotation in annotations if annotation["name"] == name]

    @unittest.skip("TODO")
    def test_pdf_with_text_style(self) -> None:
        file_name = "diff_styles.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="true", document_type="",
                                                    need_pdf_table_analysis="false"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual('1.1TimesNewRomanItalicBold20\n', node['text'])
        self.assertIn({'start': 0, 'end': 28, "name": "size", 'value': '20.0'}, node['annotations'])

        node = self._get_by_tree_path(tree, "0.1")
        annotations_size = self.__filter_by_name(name="size", annotations=node['annotations'])
        self.assertIn({'start': 0, 'end': 26, "name": "size", 'value': '16.0'}, annotations_size)
        self.assertEqual(len(node['annotations']), 5)
        self.assertEqual("Different styles(Arial16):\n", node["text"])

        node = self._get_by_tree_path(tree, "0.2.2")
        self.assertEqual('3. TimesNewRomanItalic14, Calibri18, Tahoma16\n', node['text'])
        self.assertEqual('3. ', node['text'][0:3])
        self.assertIn({'start': 0, 'end': 36, 'name': "style", 'value': 'TimesNewRomanPSMT'}, node['annotations'])
        self.assertIn({'start': 0, 'end': 2, "name": "size", 'value': '16.0'}, node['annotations'])
        self.assertEqual('TimesNewRomanItalic14, ', node['text'][3:26])
        self.assertIn({'start': 0, 'end': 36, "name": "style", 'value': 'TimesNewRomanPSMT'}, node['annotations'])
        self.assertIn({'start': 3, 'end': 25, "name": "size", 'value': '14.0'}, node['annotations'])
        self.assertEqual('Calibri18, ', node['text'][26:37])
        self.assertIn({'start': 0, 'end': 36, "name": "style", 'value': 'TimesNewRomanPSMT'}, node['annotations'])
        self.assertIn({'start': 26, 'end': 36, 'value': '18.0', "name": "size"}, node['annotations'])
        self.assertEqual('Tahoma16\n', node['text'][37:46])
        self.assertIn({'start': 37, 'end': 45, 'value': 'Tahoma', "name": "style"}, node['annotations'])
        self.assertIn({'start': 37, 'end': 45, "name": "size", 'value': '16.0'}, node['annotations'])
        self.assertEqual(9, len(node['annotations']))

    def test_pdf_with_text_style_2(self) -> None:
        file_name = "2-column-state.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="true", need_pdf_table_analysis="false"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        subs = tree['subparagraphs']
        sub = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("Compromising Tor Anonymity\n", sub['text'][0:27])
        annotations_size = self.__filter_by_name(name="size", annotations=subs[0]['annotations'])
        self.assertIn({'start': 0, 'end': 61, "name": "size", 'value': '18.0'}, annotations_size)

        annotations_style = self.__filter_by_name(name="style", annotations=subs[0]['annotations'])
        self.assertIn({'start': 0, 'end': 61, 'name': 'style', 'value': 'Helvetica-Bold'}, annotations_style)

        annotations_bold = self.__filter_by_name(name="bold", annotations=subs[0]['annotations'])
        self.assertIn({'start': 0, 'end': 61, 'name': 'bold', 'value': "True"}, annotations_bold)

        self.assertIn("Pere Manils, Abdelberi Chaabane, Stevens Le Blond,", self._get_by_tree_path(tree, "0.1")["text"])

    @unittest.skip("TODO")
    def test_pdf_with_2_columns_text(self) -> None:
        file_name = "2-column-state.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="true", document_type="",
                                                    need_pdf_table_analysis="false"))

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self.assertIn("Privacy of users in P2P networks goes far beyond their\n"
                      "current usage and is a fundamental requirement to the adop-\n"
                      "tion of P2P protocols for legal usage. In a climate of cold",
                      self._get_by_tree_path(tree, "0.5")['text'])

        self.assertIn("Keywords", self._get_by_tree_path(tree, "0.6")['text'])
        self.assertIn("Anonymizing Networks, Privacy, Tor, BitTorrent", self._get_by_tree_path(tree, "0.7")['text'])

        self.assertIn("INTRODUCTION\n", self._get_by_tree_path(tree, "0.8.0.0")["text"])
        self.assertIn("The Tor network was designed to provide freedom\n"
                      "of speech by guaranteeing anonymous communications.\n"
                      "Whereas the cryptographic foundations of Tor, based on\n"
                      "onion-routing [3, 9, 22, 24], are known to be robust, identity",
                      self._get_by_tree_path(tree, "0.8.0.1")["text"])

    def test_pdf_with_2_columns_text_2(self) -> None:
        file_name = "liters_state.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="true", need_pdf_table_analysis="false"))

        tree = result["content"]["structure"]

        self.assertIn("References", self._get_by_tree_path(tree, "0.0")["text"])
        self.assertIn("[1] Navaneeth Bodla, Bharat Singh, Rama Chellappa, and",
                      self._get_by_tree_path(tree, "0.1")["text"])

    def test_pdf_with_some_tables(self) -> None:
        file_name = "VVP_6_tables.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="true"))
        content = result["content"]
        self._test_table_refs(content)
        tree = content["structure"]
        self._check_tree_sanity(tree)

        # checks indentations
        par = self._get_by_tree_path(tree, "0.4.0.0")
        self.assertIn({'end': 170, 'value': '600', 'name': 'indentation', 'start': 0}, par["annotations"])
        self.assertIn("Методика расчета ВВП по доходам характеризуется суммой национального\n", par["text"])

    def test_pdf_with_only_table(self) -> None:
        file_name = "VVP_global_table.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="true"))

        self.assertTrue(result["content"]["tables"][0]["metadata"]["uid"] ==
                        result["content"]["structure"]["subparagraphs"][0]["annotations"][0]["value"])

    def test_pdf_with_only_mp_table(self) -> None:
        file_name = os.path.join("..", "tables", "multipage_table.pdf")
        result = self._send_request(file_name, dict(pdf_with_text_layer="true", need_header_footer_analysis=True))

        table_refs = [ann["value"] for ann in result["content"]["structure"]["subparagraphs"][0]["annotations"]
                      if ann["name"] == "table"]

        self.assertTrue(len(result["content"]["tables"]), len(table_refs))
        for table in result["content"]["tables"]:
            self.assertTrue(table["metadata"]["uid"] in table_refs)
