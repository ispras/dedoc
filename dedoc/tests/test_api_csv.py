from dedoc.tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    def test_csv_books2(self):
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


    def test_csv(self):
        file_name = "csv_coma.csv"
        result = self._send_request(file_name)
        tables = result["content"]["tables"]
        self.__check_content(tables)


    def test_csv_semicolon(self):
        file_name = "csv_semicolon.csv"
        result = self._send_request(file_name, dict(delimiter=";"))
        tables = result["content"]["tables"]
        self.__check_content(tables)