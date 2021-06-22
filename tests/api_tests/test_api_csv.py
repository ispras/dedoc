from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiCSVReader(AbstractTestApiDocReader):

    def __check_content(self, tables):
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

    def __check_content_tree(self, result: dict):
        table = result["content"]["structure"]["subparagraphs"][0]
        row1 = table["subparagraphs"][0]
        row2 = table["subparagraphs"][1]
        row3 = table["subparagraphs"][2]
        cell1_1 = row1["subparagraphs"][0]
        self.assertEqual("1", cell1_1["text"])

        cell1_2 = row1["subparagraphs"][1]
        self.assertEqual("2", cell1_2["text"])

        cell1_3 = row1["subparagraphs"][2]
        self.assertEqual("3", cell1_3["text"])

        cell2_1 = row2["subparagraphs"][0]
        self.assertEqual("2", cell2_1["text"])

        cell2_2 = row2["subparagraphs"][1]
        self.assertEqual("1", cell2_2["text"])

        cell2_3 = row2["subparagraphs"][2]
        self.assertEqual("5", cell2_3["text"])

        cell3_1 = row3["subparagraphs"][0]
        self.assertEqual("5", cell3_1["text"])

        cell3_2 = row3["subparagraphs"][1]
        self.assertEqual("3", cell3_2["text"])

        cell3_3 = row3["subparagraphs"][2]
        self.assertEqual("1", cell3_3["text"])

    def test_csv(self):
        file_name = "csv_coma.csv"
        result = self._send_request(file_name)
        self.assertIn("delimiter is ','", result["warnings"])
        tables = result["content"]["tables"]
        self.__check_content(tables)

    def test_csv_patch_table(self):
        file_name = "csv_coma.csv"
        result = self._send_request(file_name, data={"insert_table": "true", "structure_type": "tree"})
        tables = result["content"]["tables"]
        self.__check_content(tables)
        self.__check_content_tree(result)

    def test_tsv(self):
        file_name = "csv_tab.tsv"
        result = self._send_request(file_name, data={"insert_table": "true", "structure_type": "tree"})
        self.assertIn("delimiter is '\t'", result["warnings"])
        tables = result["content"]["tables"]
        self.__check_content(tables)
        self.__check_content_tree(result)

    def test_csv_semicolon(self):
        file_name = "csv_semicolon.csv"
        result = self._send_request(file_name, dict(delimiter=";", insert_table="true", structure_type="tree"))
        self.assertIn("delimiter is ';'", result["warnings"])
        tables = result["content"]["tables"]
        self.__check_content(tables)
        self.__check_content_tree(result)

    def test_csv_books(self):
        file_name = "books.csv"
        result = self._send_request(file_name)
        self.assertIn("delimiter is ','", result["warnings"])
        tables = result["content"]["tables"]
        table = tables[0]["cells"]
        self.assertListEqual(["id", "cat", "name", "price", "inStock", "author", "series_t", "sequence_i", "genre_s"],
                             table[0])
        self.assertListEqual(
            ["055357342X", "book", "A Storm of Swords", "7.99", "true", "George R.R. Martin", "A Song of Ice and Fire",
             "3", "fantasy"], table[3])

    def test_csv_books2(self):
        file_name = "books_2.csv"
        result = self._send_request(file_name)
        self.assertIn("delimiter is ','", result["warnings"])
        tables = result["content"]["tables"]
        table = tables[0]["cells"]
        self.assertListEqual(['0553573403', 'book', "A Game of Throne, kings and other stuff",
                              '7.99', 'True', 'George R.R. Martin', 'A Song of Ice and Fire', '1', 'fantasy'],
                             table[1])
        self.assertListEqual(
            ["0553579908", "book", 'A Clash of "Kings"', '7.99', 'True', 'George R.R. Martin',
             'A Song of Ice and Fire', '2', 'fantasy'], table[2])
