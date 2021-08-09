from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader
from tests.test_utils import get_by_tree_path


class TestApiDocReader(AbstractTestApiDocReader):

    def test_broken_conversion(self):
        file_name = "broken.odt"
        result = self._send_request(file_name, expected_code=415)

    def test_doc(self):
        file_name = "example.doc"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        self.__check_doc_like(result)

        self._check_metainfo(result['metadata'], 'application/msword', file_name)

    def test_docx(self):
        file_name = "example.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        self.__check_doc_like(result)

        self._check_metainfo(result['metadata'],
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document', file_name)

    def test_odt(self):
        file_name = "example.odt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        self.__check_doc_like(result)

        self._check_metainfo(result['metadata'], 'application/vnd.oasis.opendocument.text', file_name)

    def __check_doc_like(self, result):
        content = result["content"]["structure"]
        self.assertEqual("", get_by_tree_path(content, "0")["text"])
        self.assertEqual("Пример документа", get_by_tree_path(content, "0.0")["text"])
        self.assertEqual("Глава 1", get_by_tree_path(content, "0.1")["text"])
        self.assertEqual("Какие то определения", get_by_tree_path(content, "0.1.0")["text"])
        self.assertEqual("Статья 1", get_by_tree_path(content, "0.1.1")["text"])
        self.assertEqual("Статья 2", get_by_tree_path(content, "0.1.2")["text"])
        self.assertEqual("Определим опрделения", get_by_tree_path(content, "0.1.1.0")["text"])
        self.assertEqual("Дадим пояснения", get_by_tree_path(content, "0.1.2.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1")["text"])
        self.assertEqual("1.2.1. Поясним за непонятное", get_by_tree_path(content, "0.1.2.1.0")["text"])
        self.assertEqual("1.2.2. Поясним за понятное", get_by_tree_path(content, "0.1.2.1.1")["text"])
        self.assertEqual("1.2.3.", get_by_tree_path(content, "0.1.2.1.2")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.1.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.0")["text"])
        self.assertEqual("	а) это даже ежу понятно", get_by_tree_path(content, "0.1.2.1.1.0.0")["text"])
        self.assertEqual("	б) это ежу не понятно", get_by_tree_path(content, "0.1.2.1.1.0.1")["text"])

        table1, table2 = result["content"]["tables"]

        self.assertListEqual(["N", "Фамилия", "Имя", "Организация", "Телефон", "Примечания"],
                             table1["cells"][0])
        self.assertListEqual(["1", "Иванов", "Иван", "ИСП", "8-800", ""], table1["cells"][1])

        self.assertListEqual(["Фамилия", "Имя", "Отчество"], table2["cells"][0])
        self.assertListEqual(["Иванов", "Иван", "Иванович"], table2["cells"][1])
        self.assertListEqual(["Петров", "Пётр", "Петрович"], table2["cells"][2])
        self.assertListEqual(["Сидоров", "Сидор", "Сидорович"], table2["cells"][3])

        metadata = result["metadata"]
        self.assertTrue(metadata["file_name"].startswith("example"))
        self.assertTrue(metadata["modified_time"] is not None)
        self.assertTrue(metadata["created_time"] is not None)
        self.assertTrue(metadata["access_time"] is not None)
        self.assertIn("modified_date", metadata["other_fields"])

    def test_bin_file(self):
        self._send_request("file.bin", expected_code=415)

    def test_broken_docx(self):
        self._send_request("broken.docx", expected_code=415)

    def test_send_wo_file(self):
        self._send_request_wo_file(expected_code=400)

    def test_return_html(self):
        file_name = "example.doc"
        result = self._send_request(file_name, data={"structure_type": "tree", "return_format": "html"})
        self.assertTrue("<p>  <strong></strong>     <sub> id = 0 ; type = root </sub></p><p> &nbsp;&nbsp;&nbsp;&nbsp; "
                        "<b>Пример документа</b>" in result)
        self.assertTrue("<tbody>\n"
                        "<tr>\n"
                        "<td >N</td>\n"
                        "<td >Фамилия</td>\n"
                        "<td >Имя</td>\n"
                        "<td >Организация</td>\n"
                        "<td >Телефон</td>\n"
                        "<td >Примечания</td>\n"
                        "</tr>" in result)

    def test_newline_tree(self):
        file_name = "inspector.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        self.assertTrue(content["subparagraphs"][0]["text"].startswith("КАКОЕ-ТО ЗАДАНИЕ"))

    def test_doc_insert_table(self):
        file_name = "example.doc"
        result = self._send_request(file_name, data=dict(structure_type="tree", insert_table=True))
        self.__check_doc_like_insert_table(result)
        self._check_metainfo(result['metadata'], 'application/msword', file_name)

    def test_docx_insert_table(self):
        file_name = "example.docx"
        result = self._send_request(file_name, data=dict(structure_type="tree", insert_table=True))
        self.__check_doc_like_insert_table(result)

        self._check_metainfo(result['metadata'],
                             'application/vnd.openxmlformats-officedocument.wordprocessingml.document', file_name)

    def test_odt_insert_table(self):
        file_name = "example.odt"
        result = self._send_request(file_name, data=dict(structure_type="tree", insert_table=True))
        self.__check_doc_like_insert_table(result)

        self._check_metainfo(result['metadata'], 'application/vnd.oasis.opendocument.text', file_name)

    def __check_doc_like_insert_table(self, result: dict):
        content = result["content"]["structure"]
        self.assertEqual("", get_by_tree_path(content, "0")["text"])
        self.assertEqual("Пример документа", get_by_tree_path(content, "0.0")["text"])
        self.assertEqual("Глава 1", get_by_tree_path(content, "0.1")["text"])
        self.assertEqual("Какие то определения", get_by_tree_path(content, "0.1.0")["text"])
        self.assertEqual("Статья 1", get_by_tree_path(content, "0.1.1")["text"])
        self.assertEqual("Статья 2", get_by_tree_path(content, "0.1.2")["text"])
        self.assertEqual("Определим опрделения", get_by_tree_path(content, "0.1.1.0")["text"])
        self.assertEqual("Дадим пояснения", get_by_tree_path(content, "0.1.2.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.0.0")["text"])
        self.assertEqual("1.2.1. Поясним за непонятное", get_by_tree_path(content, "0.1.2.1.0")["text"])
        self.assertEqual("1.2.2. Поясним за понятное", get_by_tree_path(content, "0.1.2.1.1")["text"])
        self.assertEqual("1.2.3.", get_by_tree_path(content, "0.1.2.1.2")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.0.0.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.0.0.1")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.1.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.1")["text"])
        self.assertEqual("N", get_by_tree_path(content, "0.1.2.0.0.0.0")["text"])
        self.assertEqual("Фамилия", get_by_tree_path(content, "0.1.2.0.0.0.1")["text"])
        self.assertEqual("Имя", get_by_tree_path(content, "0.1.2.0.0.0.2")["text"])
        self.assertEqual("Организация", get_by_tree_path(content, "0.1.2.0.0.0.3")["text"])
        self.assertEqual("Телефон", get_by_tree_path(content, "0.1.2.0.0.0.4")["text"])
        self.assertEqual("Примечания", get_by_tree_path(content, "0.1.2.0.0.0.5")["text"])
        self.assertEqual("1", get_by_tree_path(content, "0.1.2.0.0.1.0")["text"])
        self.assertEqual("Иванов", get_by_tree_path(content, "0.1.2.0.0.1.1")["text"])
        self.assertEqual("Иван", get_by_tree_path(content, "0.1.2.0.0.1.2")["text"])
        self.assertEqual("ИСП", get_by_tree_path(content, "0.1.2.0.0.1.3")["text"])
        self.assertEqual("8-800", get_by_tree_path(content, "0.1.2.0.0.1.4")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.0.0.1.5")["text"])
        self.assertEqual("	а) это даже ежу понятно", get_by_tree_path(content, "0.1.2.1.1.0.0")["text"])
        self.assertEqual("	б) это ежу не понятно", get_by_tree_path(content, "0.1.2.1.1.0.1")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.0.0")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.0.1")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.0.2")["text"])
        self.assertEqual("", get_by_tree_path(content, "0.1.2.1.2.0.3")["text"])
        self.assertEqual("Фамилия", get_by_tree_path(content, "0.1.2.1.2.0.0.0")["text"])
        self.assertEqual("Имя", get_by_tree_path(content, "0.1.2.1.2.0.0.1")["text"])
        self.assertEqual("Отчество", get_by_tree_path(content, "0.1.2.1.2.0.0.2")["text"])
        self.assertEqual("Иванов", get_by_tree_path(content, "0.1.2.1.2.0.1.0")["text"])
        self.assertEqual("Иван", get_by_tree_path(content, "0.1.2.1.2.0.1.1")["text"])
        self.assertEqual("Иванович", get_by_tree_path(content, "0.1.2.1.2.0.1.2")["text"])
        self.assertEqual("Петров", get_by_tree_path(content, "0.1.2.1.2.0.2.0")["text"])
        self.assertEqual("Пётр", get_by_tree_path(content, "0.1.2.1.2.0.2.1")["text"])
        self.assertEqual("Петрович", get_by_tree_path(content, "0.1.2.1.2.0.2.2")["text"])
        self.assertEqual("Сидоров", get_by_tree_path(content, "0.1.2.1.2.0.3.0")["text"])
        self.assertEqual("Сидор", get_by_tree_path(content, "0.1.2.1.2.0.3.1")["text"])
        self.assertEqual("Сидорович", get_by_tree_path(content, "0.1.2.1.2.0.3.2")["text"])
