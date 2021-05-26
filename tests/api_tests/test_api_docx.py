from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

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

    def __check_doc_like(self, result):
        content = result["content"]["structure"]
        self.assertEqual("Пример документа", content["subparagraphs"][0]["text"])
        self.assertEqual("Глава 1", content["subparagraphs"][1]["text"])
        self.assertEqual("Статья 1", content["subparagraphs"][1]["subparagraphs"][1]["text"])
        self.assertEqual("Статья 2", content["subparagraphs"][1]["subparagraphs"][2]["text"])
        self.assertEqual("Дадим пояснения",
                         content["subparagraphs"][1]["subparagraphs"][2]["subparagraphs"][0]['text'])

        lst = content["subparagraphs"][1]["subparagraphs"][2]["subparagraphs"][1]
        self.assertEqual("1.2.1. Поясним за непонятное", lst["subparagraphs"][0]["text"])
        self.assertEqual("1.2.2. Поясним за понятное", lst["subparagraphs"][1]["text"])
        self.assertEqual("а) это даже ежу понятно",
                         lst["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][0]["text"].strip())
        self.assertEqual("б) это ежу не понятно",
                         lst["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][1]["text"].strip())
        self.assertEqual("1.2.3.", lst["subparagraphs"][2]["text"])

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

    def test_odt(self):
        file_name = "example.odt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        self.__check_doc_like(result)

        self._check_metainfo(result['metadata'], 'application/vnd.oasis.opendocument.text', file_name)

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
        self.assertTrue(content["subparagraphs"][0]["text"].startswith("КАКОЕ-ТО ЗАДАНИЕ\nНА ЧТО-ТО ТАМ ПОЛЕЗНОЕ\n\n"))
