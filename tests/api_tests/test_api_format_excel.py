import os
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiExcelReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "xlsx")

    def __check_content(self, tables: List[dict]) -> None:
        self.assertEqual(2, len(tables))
        table1 = tables[0]
        table2 = tables[1]

        self.assertListEqual(["1.0", "2.0", "3.0"], self._get_text_of_row(table1["cells"][0]))
        self.assertListEqual(["4.0", "5.0", "6.0"], self._get_text_of_row(table1["cells"][1]))

        self.assertListEqual(["11.0", "22.0", "33.0", "44.0"], self._get_text_of_row(table2["cells"][0]))
        self.assertListEqual(["55.0", "66.0", "77.0", "88.0"], self._get_text_of_row(table2["cells"][1]))

    def test_ods(self) -> None:
        file_name = "example.ods"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_xlsx(self) -> None:
        file_name = "example.xlsx"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_xls(self) -> None:
        file_name = "example.xls"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_ods_formulas(self) -> None:
        file_name = "example_formulas.ods"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content_formulas(tables)

    def test_xls_formulas(self) -> None:
        file_name = "example_formulas.xls"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content_formulas(tables)

    def test_xlsx_formulas(self) -> None:
        file_name = "example_formulas.xlsx"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content_formulas(tables)

    def __check_content_formulas(self, tables: List[dict]) -> None:
        self.assertEqual(2, len(tables))
        table1, table2 = (table["cells"] for table in tables)

        self.assertListEqual(["a", "b", "c"], self._get_text_of_row(table1[0]))
        self.assertListEqual(["1.0", "2.0", "3.0"], self._get_text_of_row(table1[1]))
        self.assertListEqual(["3.0", "4.0", "7.0"], self._get_text_of_row(table1[2]))
        self.assertListEqual(["2.0", "3.0", "5.0"], self._get_text_of_row(table1[3]))
        self.assertListEqual(["5.0", "6.0", "11.0"], self._get_text_of_row(table1[4]))
        self.assertListEqual(["7.0", "33.0", "40.0"], self._get_text_of_row(table1[5]))

        self.assertListEqual(["r", "p", "s", "pi"], self._get_text_of_row(table2[0]))
        self.assertListEqual(["1.0", "6.28", "3.14", "3.14"], self._get_text_of_row(table2[1]))
        self.assertListEqual(["2.0", "12.56", "12.56", ""], self._get_text_of_row(table2[2]))
        self.assertListEqual(["3.0", "18.84", "28.26", ""], self._get_text_of_row(table2[3]))
        self.assertListEqual(["4.0", "25.12", "50.24", ""], self._get_text_of_row(table2[4]))
        self.assertListEqual(["5.0", "31.4", "78.5", ""], self._get_text_of_row(table2[5]))
        self.assertListEqual(["6.0", "37.68", "113.04", ""], self._get_text_of_row(table2[6]))
        self.assertListEqual(["7.0", "43.96", "153.86", ""], self._get_text_of_row(table2[7]))
        self.assertListEqual(["8.0", "50.24", "200.96", ""], self._get_text_of_row(table2[8]))
