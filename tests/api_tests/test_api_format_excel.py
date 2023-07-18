import os
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiExcelReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "xlsx")

    def __check_content(self, tables: List[dict]) -> None:
        self.assertEqual(2, len(tables))
        table1 = tables[0]
        table2 = tables[1]

        rows1 = table1["cells"]
        rows2 = table2["cells"]

        self.assertEqual("1.0", rows1[0][0])
        self.assertEqual("2.0", rows1[0][1])
        self.assertEqual("3.0", rows1[0][2])
        self.assertEqual("4.0", rows1[1][0])
        self.assertEqual("5.0", rows1[1][1])
        self.assertEqual("6.0", rows1[1][2])

        self.assertEqual("11.0", rows2[0][0])
        self.assertEqual("22.0", rows2[0][1])
        self.assertEqual("33.0", rows2[0][2])
        self.assertEqual("44.0", rows2[0][3])
        self.assertEqual("55.0", rows2[1][0])
        self.assertEqual("66.0", rows2[1][1])
        self.assertEqual("77.0", rows2[1][2])
        self.assertEqual("88.0", rows2[1][3])

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

        self.assertListEqual(['a', 'b', 'c'], table1[0])
        self.assertListEqual(['1.0', '2.0', '3.0'], table1[1])
        self.assertListEqual(['3.0', '4.0', '7.0'], table1[2])
        self.assertListEqual(['2.0', '3.0', '5.0'], table1[3])
        self.assertListEqual(['5.0', '6.0', '11.0'], table1[4])
        self.assertListEqual(['7.0', '33.0', '40.0'], table1[5])

        self.assertListEqual(['r', 'p', 's', 'pi'], table2[0])
        self.assertListEqual(['1.0', '6.28', '3.14', '3.14'], table2[1])
        self.assertListEqual(['2.0', '12.56', '12.56', ''], table2[2])
        self.assertListEqual(['3.0', '18.84', '28.26', ''], table2[3])
        self.assertListEqual(['4.0', '25.12', '50.24', ''], table2[4])
        self.assertListEqual(['5.0', '31.4', '78.5', ''], table2[5])
        self.assertListEqual(['6.0', '37.68', '113.04', ''], table2[6])
        self.assertListEqual(['7.0', '43.96', '153.86', ''], table2[7])
        self.assertListEqual(['8.0', '50.24', '200.96', ''], table2[8])
