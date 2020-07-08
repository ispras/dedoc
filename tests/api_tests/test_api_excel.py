from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiExcelReader(AbstractTestApiDocReader):

    def __check_content(self, tables):
        self.assertEqual(2, len(tables))
        table1 = tables[0]
        table2 = tables[1]

        rows1 = table1["cells"]
        rows2 = table2["cells"]

        self.assertEqual(1, rows1[0][0])
        self.assertEqual(2, rows1[0][1])
        self.assertEqual(3, rows1[0][2])
        self.assertEqual(4, rows1[1][0])
        self.assertEqual(5, rows1[1][1])
        self.assertEqual(6, rows1[1][2])

        self.assertEqual(11, rows2[0][0])
        self.assertEqual(22, rows2[0][1])
        self.assertEqual(33, rows2[0][2])
        self.assertEqual(44, rows2[0][3])
        self.assertEqual(55, rows2[1][0])
        self.assertEqual(66, rows2[1][1])
        self.assertEqual(77, rows2[1][2])
        self.assertEqual(88, rows2[1][3])

    def test_ods(self):
        file_name = "example.ods"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_xlsx(self):
        file_name = "example.xlsx"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_xls(self):
        file_name = "example.xls"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)


