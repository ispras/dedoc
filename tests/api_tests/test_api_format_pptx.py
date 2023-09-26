import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPPTXReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "pptx")

    def test_pptx(self) -> None:
        file_name = "example.pptx"
        result = self._send_request(file_name, data=dict(structure_type="linear"))
        self.__check_content(result["content"])

    def test_ppt(self) -> None:
        file_name = "example.ppt"
        result = self._send_request(file_name, data=dict(structure_type="linear"))
        self.__check_content(result["content"])

    def test_odp(self) -> None:
        file_name = "example.odp"
        result = self._send_request(file_name, data=dict(structure_type="linear"))
        self.__check_content(result["content"])

    def __check_content(self, content: dict) -> None:
        subparagraphs = content["structure"]["subparagraphs"]
        self.assertEqual("A long time ago in a galaxy far far away ", subparagraphs[0]["text"])
        self.assertEqual("Example", subparagraphs[1]["text"])
        self.assertEqual("Some author", subparagraphs[2]["text"])
        self.assertEqual("This is simple table", subparagraphs[3]["text"])

        table = content["tables"][0]["cells"]
        self.assertListEqual(["", "Header1", "Header2", "Header3"], self._get_text_of_row(table[0]))
        self.assertListEqual(["Some content", "A", "B", "C"], self._get_text_of_row(table[1]))
