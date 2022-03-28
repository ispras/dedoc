import os
from typing import List

from tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "csvs")

    def test_csv_books2(self) -> None:
        file_name = "books_2.csv"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        table = tables[0]["cells"]
        self.assertListEqual(['0553573403', 'book', "A Game of Throne, kings and other stuff",
                              '7.99', 'True', 'George R.R. Martin', 'A Song of Ice and Fire', '1', 'fantasy'],
                             table[1])
        self.assertListEqual(
            ["0553579908", "book", 'A Clash of "Kings"', '7.99', 'True', 'George R.R. Martin',
             'A Song of Ice and Fire', '2', 'fantasy'], table[2])

    def test_csv(self) -> None:
        file_name = "csv_coma.csv"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_csv_semicolon(self) -> None:
        file_name = "csv_semicolon.csv"
        result = self._send_request(file_name, dict(delimiter=";"))
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def __check_content(self, tables: List[dict]) -> None:
        self.assertEqual(1, len(tables))
        table1 = tables[0]
        rows1 = table1["cells"]

        self.assertEqual("1", rows1[0][0])
        self.assertEqual("2", rows1[0][1])
        self.assertEqual('3', rows1[0][2])

        self.assertEqual("2", rows1[1][0])
        self.assertEqual("1", rows1[1][1])
        self.assertEqual("5", rows1[1][2])

        self.assertEqual("5", rows1[2][0])
        self.assertEqual("3", rows1[2][1])
        self.assertEqual("1", rows1[2][2])
