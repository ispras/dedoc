import os
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiCSVReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "csvs")

    def test_csv(self) -> None:
        file_name = "csv_coma.csv"
        result = self._send_request(file_name)
        self.assertIn("delimiter is ','", result["warnings"])
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_csv_encoding(self) -> None:
        for file_name in ("utf-8.csv", "cp1251.csv", "utf-8.tsv", "cp1251.tsv"):
            result = self._send_request(file_name)
            tables = result["content"]["tables"]
            self.assertEqual(1, len(tables))
            table = tables[0]["cells"]
            row0 = self._get_text_of_row(table[0])
            row1 = self._get_text_of_row(table[1])
            row2 = self._get_text_of_row(table[2])
            self.assertListEqual(["имя", "фамилия", "возраст"], row0)
            self.assertListEqual(["Иванов", "Иван", "31"], row1)
            self.assertListEqual(["Алексей", "Петров", "15"], row2)

    def test_csv_books(self) -> None:
        file_name = "books.csv"
        result = self._send_request(file_name, dict(different_param="some value"))

        self.assertIn("delimiter is ','", result["warnings"])
        self.assertIn("encoding is ascii", result["warnings"])

        tables = result["content"]["tables"]
        table = tables[0]["cells"]
        row0 = self._get_text_of_row(table[0])
        row3 = self._get_text_of_row(table[3])
        self.assertListEqual(["id", "cat", "name", "price", "inStock", "author", "series_t", "sequence_i", "genre_s"], row0)
        self.assertListEqual(["055357342X", "book", "A Storm of Swords", "7.99", "true", "George R.R. Martin", "A Song of Ice and Fire", "3", "fantasy"], row3)

    def test_csv_books2(self) -> None:
        file_name = "books_2.csv"
        result = self._send_request(file_name)
        self.assertIn("delimiter is ','", result["warnings"])
        tables = result["content"]["tables"]
        table = tables[0]["cells"]
        row1 = self._get_text_of_row(table[1])
        row2 = self._get_text_of_row(table[2])
        self.assertListEqual([
            "0553573403", "book", "A Game of Throne, kings and other stuff", "7.99", "True", "George R.R. Martin", "A Song of Ice and Fire", "1", "fantasy"
        ], row1)
        self.assertListEqual(["0553579908", "book", 'A Clash of "Kings"', "7.99", "True", "George R.R. Martin", "A Song of Ice and Fire", "2", "fantasy"], row2)

    def __check_content(self, tables: List[dict]) -> None:
        self.assertEqual(1, len(tables))
        table1 = tables[0]["cells"]

        row0 = self._get_text_of_row(table1[0])
        row1 = self._get_text_of_row(table1[1])
        row2 = self._get_text_of_row(table1[2])

        self.assertEqual("1", row0[0])
        self.assertEqual("2", row0[1])
        self.assertEqual("3", row0[2])

        self.assertEqual("2", row1[0])
        self.assertEqual("1", row1[1])
        self.assertEqual("5", row1[2])

        self.assertEqual("5", row2[0])
        self.assertEqual("3", row2[1])
        self.assertEqual("1", row2[2])
