import os

from dedoc.data_structures.concrete_annotations.linked_text_annotation import LinkedTextAnnotation
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from tests.test_utils import get_by_tree_path


class TestApiDocReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "docx")

    def test_docx_metadata(self) -> None:
        file_name = "english_doc.docx"
        result = self._send_request(file_name)
        metadata = result["metadata"]
        self.assertEqual("Тема", metadata["document_subject"])
        self.assertEqual("анализ естественных языков", metadata["keywords"])
        self.assertEqual("курсовая работа", metadata["category"])
        self.assertEqual("на 3 потянет", metadata["comments"])
        self.assertEqual("Андрей Пышкин", metadata["author"])
        self.assertEqual("Андреус Пышкинус", metadata["last_modified_by"])

    def test_docx(self) -> None:
        file_name = "example.docx"
        result = self._send_request(file_name)
        self.__check_doc_like(result)
        self._check_metainfo(result["metadata"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document", file_name)

    def test_docx_ujson(self) -> None:
        file_name = "example.docx"
        result = self._send_request(file_name, data={"return_format": "ujson"})
        self.__check_doc_like(result)

    def test_doc(self) -> None:
        file_name = "example.doc"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        self.__check_doc_like(result)
        self._check_metainfo(result["metadata"], "application/msword", file_name)

    def test_odt(self) -> None:
        file_name = "example.odt"
        result = self._send_request(file_name)
        self.__check_doc_like(result)
        self._check_metainfo(result["metadata"], "application/vnd.oasis.opendocument.text", file_name)

    def test_rtf(self) -> None:
        file_name = "example.rtf"
        result = self._send_request(file_name)
        self.__check_doc_like(result)
        self._check_metainfo(result["metadata"], "application/rtf", file_name)

    def test_odt_with_split(self) -> None:
        file_name = "ТЗ_ГИС_3  .odt"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][0]["text"].strip(), "Система должна обеспечивать защиту от несанкционированного доступа (НСД)")

    def test_broken_conversion(self) -> None:
        file_name = "broken.odt"
        result = self._send_request(file_name, expected_code=200)
        warnings = [warning for warning in result["warnings"] if warning.startswith("Incorrect extension")]
        self.assertEqual(len(warnings), 1)

    def test_footnotes(self) -> None:
        file_name = "example_footnote_endnote.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        self.__check_doc_like(result)
        full_text = []
        tree = result["content"]["structure"]
        node = get_by_tree_path(tree, "0.0")
        annotations = [(annotation["name"], annotation["value"]) for annotation in node["annotations"]]
        self.assertIn((LinkedTextAnnotation.name, "То – союз в русском языке"), annotations)
        self.assertIn((LinkedTextAnnotation.name, "В этом слове допущена опечатка"), annotations)

        stack = [tree]
        while stack:
            node = stack.pop()
            stack.extend(node["subparagraphs"])
            full_text.append(node["text"])
        full_text = "".join(full_text).lower()
        self.assertNotIn("союз", full_text)
        self.assertNotIn("васька", full_text)
        self.assertNotIn("опечатка", full_text)
        self.assertIn("определения", full_text)
        self.assertIn("понятное", full_text)

    def test_tricky_doc(self) -> None:
        file_name = "doc.docx"
        _ = self._send_request(file_name)

    def test_not_stripped_xml(self) -> None:
        self._send_request("not_stripped_xml.docx", expected_code=200)

    def test_docx_with_comments(self) -> None:
        _ = self._send_request("with_comments.docx", expected_code=200)

    def test_return_html(self) -> None:
        file_name = "example.doc"
        result = self._send_request(file_name, data={"structure_type": "tree", "return_format": "html"})
        self.assertIn("<p>  <strong></strong>     <sub> id = 0 ; type = root </sub></p><p> &nbsp;&nbsp;&nbsp;&nbsp; <b>Пример документа", result)
        self.assertTrue("<tbody>\n"
                        "<tr>\n"
                        '<td colspan="1" rowspan="1">N</td>\n'
                        '<td colspan="1" rowspan="1">Фамилия</td>\n'
                        '<td colspan="1" rowspan="1">Имя</td>\n'
                        '<td colspan="1" rowspan="1">Организация</td>\n'
                        '<td colspan="1" rowspan="1">Телефон</td>\n'
                        '<td colspan="1" rowspan="1">Примечания</td>\n'
                        "</tr>" in result)

    def test_newline_tree(self) -> None:
        file_name = "inspector.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        self.assertTrue(content["subparagraphs"][0]["text"].startswith("КАКОЕ-ТО ЗАДАНИЕ"))

    def test_docx_heading_new(self) -> None:
        file_name = "tz-1ek-20_minimum.docx"
        data = dict(structure_type="tree", return_format="html")
        _ = self._send_request(file_name, data=data)

    def test_properties_extractor(self) -> None:
        file_name = "broken_properties.docx"
        result = self._send_request(file_name, data={})
        content = result["content"]["structure"]
        self.assertEqual("FonFfff", get_by_tree_path(content, "0.0")["text"].strip())

    def test_name_with_apostrophe(self) -> None:
        file_name = "Well. Known -Nik O'Tinn -Ireland 2023- DRAFT.doc"
        _ = self._send_request(file_name, data={})

    def __check_doc_like(self, result: dict) -> None:
        content = result["content"]["structure"]
        self.assertEqual("", get_by_tree_path(content, "0")["text"])
        self.assertEqual("Пример документа\nГлава 1\nКакие то определения\nСтатья 1\nОпределим опрделения\nСтатья 2\nДадим пояснения",
                         get_by_tree_path(content, "0.0")["text"].strip())
        self.assertEqual("1.2.1. Поясним за непонятное", get_by_tree_path(content, "0.1.0")["text"].strip())
        self.assertEqual("1.2.2. Поясним за понятное", get_by_tree_path(content, "0.1.1")["text"].strip())
        self.assertEqual("1.2.3.", get_by_tree_path(content, "0.1.2")["text"].strip())
        self.assertEqual("\tа) это даже ежу понятно", get_by_tree_path(content, "0.1.1.0.0")["text"].rstrip())
        self.assertEqual("\tб) это ежу не понятно", get_by_tree_path(content, "0.1.1.0.1")["text"].rstrip())

        table1, table2 = result["content"]["tables"]

        self.assertListEqual(["N", "Фамилия", "Имя", "Организация", "Телефон", "Примечания"], self._get_text_of_row(table1["cells"][0]))
        self.assertListEqual(["1", "Иванов", "Иван", "ИСП", "8-800", ""], self._get_text_of_row(table1["cells"][1]))

        self.assertListEqual(["Фамилия", "Имя", "Отчество"], self._get_text_of_row(table2["cells"][0]))
        self.assertListEqual(["Иванов", "Иван", "Иванович"], self._get_text_of_row(table2["cells"][1]))
        self.assertListEqual(["Петров", "Пётр", "Петрович"], self._get_text_of_row(table2["cells"][2]))
        self.assertListEqual(["Сидоров", "Сидор", "Сидорович"], self._get_text_of_row(table2["cells"][3]))

        metadata = result["metadata"]
        self.assertTrue(metadata["file_name"].startswith("example"))
        self.assertTrue(metadata["modified_time"] is not None)
        self.assertTrue(metadata["created_time"] is not None)
        self.assertTrue(metadata["access_time"] is not None)
        self.assertIn("modified_date", metadata)
