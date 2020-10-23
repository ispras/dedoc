from tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    def test_doc(self):
        file_name = "example.doc"
        result = self._send_request(file_name, data=dict(structure_type="tree"))
        self.__check_doc_like(result)

        self._check_metainfo(result['metadata'], 'application/msword', file_name)

    def test_docx(self):
        file_name = "example.docx"
        result = self._send_request(file_name, data=dict(structure_type="tree"))
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

    def test_odt(self):
        file_name = "example.odt"
        result = self._send_request(file_name, data=dict(structure_type="tree"))
        self.__check_doc_like(result)

        self._check_metainfo(result['metadata'], 'application/vnd.oasis.opendocument.text', file_name)

    def test_tricky_doc(self):
        file_name = "doc.docx"
        result = self._send_request(file_name)

    def test_text(self):
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data=dict(structure_type="tree"))
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    def test_bin_file(self):
        self._send_request("file.bin", expected_code=415)
