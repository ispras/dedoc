import os

from dedoc.tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

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
        self.assertEqual("Пример документа", nodes[0]["text"])
        self.assertEqual("Какие то определения", nodes[1]["subparagraphs"][0]["text"])

    def test_incorrect_structure(self) -> None:
        file_name = "example.docx"
        _ = self._send_request(file_name, data={"structure_type": "bagel"}, expected_code=400)
