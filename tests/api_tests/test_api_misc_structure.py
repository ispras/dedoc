import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestStructure(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "docx")

    def test_linear_structure(self) -> None:
        file_name = "example.docx"
        result = self._send_request(file_name, data={"structure_type": "linear"})
        nodes = result["content"]["structure"]["subparagraphs"]
        self.assertEqual(len(nodes), 13)
        for node in nodes:
            self.assertListEqual([], node["subparagraphs"])

    def test_default_structure(self) -> None:
        file_name = "example.docx"
        result = self._send_request(file_name, data={"structure_type": "linear"})
        nodes = result["content"]["structure"]["subparagraphs"]
        self.assertEqual(len(nodes), 13)
        for node in nodes:
            self.assertListEqual([], node["subparagraphs"])

    def test_tree_structure(self) -> None:
        file_name = "example.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        nodes = result["content"]["structure"]["subparagraphs"]
        self.assertEqual(len(nodes), 2)
        self.assertEqual("Пример документа", nodes[0]["text"].split("\n")[0])
        self.assertEqual("1.2.1. Поясним за непонятное", nodes[1]["subparagraphs"][0]["text"].strip())

    def test_page_id_tree_structure(self) -> None:
        file_name = os.path.join("..", "pdf_with_text_layer", "test_page_id.pdf")
        result = self._send_request(file_name, data={"structure_type": "tree"})
        node = result["content"]["structure"]["subparagraphs"][0]

        page_change_positions = [2135, 4270, 6405, 8540, 10675, 12810, 13323]
        for idx, additional_page_id in enumerate(node["metadata"]["additional_page_ids"], start=1):
            self.assertEqual(idx, additional_page_id["page_id"])
            start, end = page_change_positions[idx - 1], page_change_positions[idx]
            self.assertEqual(start, additional_page_id["start"])
            self.assertEqual(end, additional_page_id["end"])
            self.assertFalse(node["text"][start:end].startswith("\n"))
            self.assertTrue(node["text"][start:end].endswith("\n"))

    def test_incorrect_structure(self) -> None:
        file_name = "example.docx"
        _ = self._send_request(file_name, data={"structure_type": "bagel"}, expected_code=400)
