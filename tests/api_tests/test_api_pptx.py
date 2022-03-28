import os

from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiExcelReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "pptx")

    def test_pptx(self) -> None:
        file_name = "example.pptx"
        result = self._send_request(file_name)
        self.__check_content(result['content'])

    def test_ppt(self) -> None:
        file_name = "example.ppt"
        result = self._send_request(file_name)
        self.__check_content(result['content'])

    def test_odp(self) -> None:
        file_name = "example.odp"
        result = self._send_request(file_name)
        self.__check_content(result['content'])

    def __check_content(self, content: dict) -> None:
        subparagraphs = content['structure']['subparagraphs']
        self.assertEqual('A long time ago in a galaxy far far away ', subparagraphs[0]['text'])
        self.assertEqual('Example', subparagraphs[1]['text'])
        self.assertEqual('Some author', subparagraphs[2]['text'])
        self.assertEqual('This is simple table', subparagraphs[3]['text'])

        table = content['tables'][0]['cells']
        self.assertEqual('', table[0][0])
        self.assertEqual('Header1', table[0][1])
        self.assertEqual('Header2', table[0][2])
        self.assertEqual('Header3', table[0][3])
        self.assertEqual('Some content', table[1][0])
        self.assertEqual('A', table[1][1])
        self.assertEqual('B', table[1][2])
        self.assertEqual('C', table[1][3])
