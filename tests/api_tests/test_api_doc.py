from datetime import datetime

import pytz

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDocs(AbstractTestApiDocReader):

    def test_doc(self) -> None:
        file_name = "docx/example.doc"
        result = self._send_request(file_name, data={"insert_table": True})
        self.__check_doc_like(result)

    def __get_timestamp(self, year: int, month: int, day: int) -> int:
        return int(datetime(year=year, month=month, day=day, tzinfo=pytz.utc).timestamp())

    def test_docx_metadata(self) -> None:
        file_name = "docx/english_doc.docx"
        result = self._send_request(file_name)
        metadata = result["metadata"]
        docx_metadata = metadata["other_fields"]
        self.assertEqual("Тема", docx_metadata["document_subject"])
        self.assertEqual("анализ естественных языков", docx_metadata["keywords"])
        self.assertEqual("курсовая работа", docx_metadata["category"])
        self.assertEqual("на 3 потянет", docx_metadata["comments"])
        self.assertEqual("Андрей Пышкин", docx_metadata["author"])
        self.assertEqual("Андреус Пышкинус", docx_metadata["last_modified_by"])

    def test_docx(self) -> None:
        file_name = "docx/example.docx"
        result = self._send_request(file_name, data={"insert_table": True})
        self.__check_doc_like(result)

    def test_docx_ujson(self) -> None:
        file_name = "docx/example.docx"
        result = self._send_request(file_name, data={"insert_table": True, "return_format": "ujson"})
        self.__check_doc_like(result)

    def test_odt(self) -> None:
        file_name = "docx/example.odt"
        result = self._send_request(file_name, data={"insert_table": True})
        self.__check_doc_like(result)

    def __check_doc_like(self, result: dict) -> None:
        content = result["content"]["structure"]

        self._check_tree_sanity(content)
        self.assertEqual("", self._get_by_tree_path(content, "0")["text"])
        self.assertEqual("Пример документа", self._get_by_tree_path(content, "0.0")["text"])
        self.assertEqual("Глава 1", self._get_by_tree_path(content, "0.1")["text"])
        self.assertEqual("Какие то определения", self._get_by_tree_path(content, "0.1.0")["text"])
        self.assertEqual("Статья 1", self._get_by_tree_path(content, "0.1.1")["text"])
        self.assertEqual("Статья 2", self._get_by_tree_path(content, "0.1.2")["text"])
        self.assertEqual("Определим опрделения", self._get_by_tree_path(content, "0.1.1.0")["text"])
        self.assertEqual("Дадим пояснения", self._get_by_tree_path(content, "0.1.2.0")["text"])
        self.assertEqual("", self._get_by_tree_path(content, "0.1.2.1")["text"])
        self.assertEqual("1.2.1. Поясним за непонятное", self._get_by_tree_path(content, "0.1.2.1.0")["text"])
        self.assertEqual("1.2.2. Поясним за понятное", self._get_by_tree_path(content, "0.1.2.1.1")["text"])
        self.assertEqual("1.2.3.", self._get_by_tree_path(content, "0.1.2.1.2")["text"])
        self.assertEqual("", self._get_by_tree_path(content, "0.1.2.1.1.0")["text"])
        self.assertEqual("	а) это даже ежу понятно", self._get_by_tree_path(content, "0.1.2.1.1.0.0")["text"])
        self.assertEqual("	б) это ежу не понятно", self._get_by_tree_path(content, "0.1.2.1.1.0.1")["text"])
        self.assertEqual("N", self._get_by_tree_path(content, "0.1.2.0.0.0.0")["text"])
        self.assertEqual("Фамилия", self._get_by_tree_path(content, "0.1.2.0.0.0.1")["text"])
        self.assertEqual("Имя", self._get_by_tree_path(content, "0.1.2.0.0.0.2")["text"])
        self.assertEqual("Организация", self._get_by_tree_path(content, "0.1.2.0.0.0.3")["text"])
        self.assertEqual("Телефон", self._get_by_tree_path(content, "0.1.2.0.0.0.4")["text"])
        self.assertEqual("Примечания", self._get_by_tree_path(content, "0.1.2.0.0.0.5")["text"])
        self.assertEqual("1", self._get_by_tree_path(content, "0.1.2.0.0.1.0")["text"])
        self.assertEqual("Иванов", self._get_by_tree_path(content, "0.1.2.0.0.1.1")["text"])
        self.assertEqual("Иван", self._get_by_tree_path(content, "0.1.2.0.0.1.2")["text"])
        self.assertEqual("ИСП", self._get_by_tree_path(content, "0.1.2.0.0.1.3")["text"])
        self.assertEqual("8-800", self._get_by_tree_path(content, "0.1.2.0.0.1.4")["text"])
        self.assertEqual("", self._get_by_tree_path(content, "0.1.2.0.0.1.5")["text"])
        self.assertEqual("Фамилия", self._get_by_tree_path(content, "0.1.2.1.2.0.0.0")["text"])
        self.assertEqual("Имя", self._get_by_tree_path(content, "0.1.2.1.2.0.0.1")["text"])
        self.assertEqual("Отчество", self._get_by_tree_path(content, "0.1.2.1.2.0.0.2")["text"])
        self.assertEqual("Иванов", self._get_by_tree_path(content, "0.1.2.1.2.0.1.0")["text"])
        self.assertEqual("Иван", self._get_by_tree_path(content, "0.1.2.1.2.0.1.1")["text"])
        self.assertEqual("Иванович", self._get_by_tree_path(content, "0.1.2.1.2.0.1.2")["text"])
        self.assertEqual("Петров", self._get_by_tree_path(content, "0.1.2.1.2.0.2.0")["text"])
        self.assertEqual("Пётр", self._get_by_tree_path(content, "0.1.2.1.2.0.2.1")["text"])
        self.assertEqual("Петрович", self._get_by_tree_path(content, "0.1.2.1.2.0.2.2")["text"])
        self.assertEqual("Сидоров", self._get_by_tree_path(content, "0.1.2.1.2.0.3.0")["text"])
        self.assertEqual("Сидор", self._get_by_tree_path(content, "0.1.2.1.2.0.3.1")["text"])
        self.assertEqual("Сидорович", self._get_by_tree_path(content, "0.1.2.1.2.0.3.2")["text"])

        table1, table2 = result["content"]["tables"]

        self.assertListEqual(["N", "Фамилия", "Имя", "Организация", "Телефон", "Примечания"],
                             table1["cells"][0])
        self.assertListEqual(["1", "Иванов", "Иван", "ИСП", "8-800", ""], table1["cells"][1])

        self.assertListEqual(["Фамилия", "Имя", "Отчество"], table2["cells"][0])
        self.assertListEqual(["Иванов", "Иван", "Иванович"], table2["cells"][1])
        self.assertListEqual(["Петров", "Пётр", "Петрович"], table2["cells"][2])
        self.assertListEqual(["Сидоров", "Сидор", "Сидорович"], table2["cells"][3])

    def test_odt_with_split(self) -> None:
        file_name = "docx/ТЗ_ГИС_3  .odt"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][0]["text"].strip(),
                         'Система должна обеспечивать защиту от несанкционированного доступа (НСД)')
