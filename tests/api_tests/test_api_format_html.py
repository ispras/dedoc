import os

from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiHtmlReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "htmls", file_name)

    def test_html(self) -> None:
        file_name = "example.html"
        result = self._send_request(file_name)
        self.__check_example_file(result, file_name)

    def test_html_cp1251(self) -> None:
        file_name = "example_cp1251.html"
        result = self._send_request(file_name)
        self.__check_example_file(result, file_name)

    def test_html_koi8(self) -> None:
        file_name = "example_koi.html"
        result = self._send_request(file_name)
        self.__check_example_file(result, file_name)

    def __check_example_file(self, result: dict, file_name: str) -> None:
        content = result["content"]
        tree = content["structure"]
        self._check_tree_sanity(tree)

        node = self._get_by_tree_path(tree, "0")
        self.assertEqual("root", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("Пример документа", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("Глава 1", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("Какие то определения", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.1")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("Статья 1", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.1.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("Определим определения  \nТекст ", node["text"].strip()[:30])
        self.assertIn({"start": 1, "end": 31, "name": "bold", "value": "True"}, node["annotations"])
        self.assertIn({"start": 46, "end": 52, "name": "bold", "value": "True"}, node["annotations"])
        self.assertIn({"start": 42, "end": 45, "name": "underlined", "value": "True"}, node["annotations"])
        self.assertIn({"start": 32, "end": 42, "name": "italic", "value": "True"}, node["annotations"])

        node = self._get_by_tree_path(tree, "0.0.0.2")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("Статья 2", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("Дадим пояснения", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.1")
        self.assertEqual("list", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.1.0")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("1.2.1.  Поясним за непонятное", node["text"].strip()[:30])
        bold = [annotation for annotation in node["annotations"] if annotation["name"] == BoldAnnotation.name]
        bold.sort(key=lambda a: a["start"])
        first, second = bold
        self.assertEqual("Поясним", node["text"][first["start"]: first["end"]].strip())
        self.assertEqual("непонятное", node["text"][second["start"]: second["end"]].strip())

        node = self._get_by_tree_path(tree, "0.0.0.2.1.1")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("1.2.2. Поясним за понятное", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.1.1.0")
        self.assertEqual("list", node["metadata"]["paragraph_type"])
        self.assertEqual("", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.1.1.0.0")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("a) это даже ежу понятно", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.1.1.0.1")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("b) это ежу не понятно", node["text"].strip()[:30])

        node = self._get_by_tree_path(tree, "0.0.0.2.1.2")
        self.assertEqual("list_item", node["metadata"]["paragraph_type"])
        self.assertEqual("1.2.3.", node["text"].strip()[:30])

        table1 = result["content"]["tables"][0]

        self.assertListEqual(["N", "Фамилия", "Имя", "Организация", "Телефон", "Примечания"], self._get_text_of_row(table1["cells"][0]))
        self.assertListEqual(["1", "Иванов", "Иван", "ИСП", "8-800", ""], self._get_text_of_row(table1["cells"][1]))

        table2 = result["content"]["tables"][1]
        self.assertListEqual(["Фамилия", "Имя", "Отчество"], self._get_text_of_row(table2["cells"][0]))
        self.assertListEqual(["Иванов", "Иван", "Иванович"], self._get_text_of_row(table2["cells"][1]))
        self.assertListEqual(["Петров", "Пётр", "Петрович"], self._get_text_of_row(table2["cells"][2]))
        self.assertListEqual(["Сидоров", "Сидор", "Сидорович"], self._get_text_of_row(table2["cells"][3]))

        self.__check_metainfo(result["metadata"], "text/html", file_name)

    def test_part_html(self) -> None:
        file_name = "part.html"
        result = self._send_request(file_name)

        content = result["content"]["structure"]
        self._check_tree_sanity(content)
        self.assertEqual("Лесные слоны", content["subparagraphs"][0]["text"].strip())
        self.assertEqual("В данном разделе мы поговорим о малоизвестных лесных слонах...", content["subparagraphs"][0]["subparagraphs"][0]["text"].strip())
        self.assertEqual("Среда обитания", content["subparagraphs"][0]["subparagraphs"][1]["text"].strip())
        self.assertEqual("Лесные слоны живут не на деревьях, а под ними.", content["subparagraphs"][0]["subparagraphs"][1]["subparagraphs"][0]["text"].strip())

    def test_plain_text_html(self) -> None:
        file_name = "plain.html"
        result = self._send_request(file_name)

        content = result["content"]["structure"]
        self._check_tree_sanity(content)
        self.assertEqual(content["subparagraphs"][0]["text"], "February 24, 2021 and some text")

    def test_html_with_styles_as_attribute(self) -> None:
        file_name = "html_with_styles.html"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        self._check_tree_sanity(content)
        annotations = content["subparagraphs"][0]["annotations"]

        text = "Some right text\nSome center text\nSome left text\n\nBIG TEXT"
        self.assertEqual(text, content["subparagraphs"][0]["text"])
        self.assertEqual(len(annotations), 4)
        for annotation in annotations:
            self.assertGreater(len(text), annotation["start"])
        self.assertIn({"name": "alignment", "value": "right", "start": 0, "end": 15}, annotations)
        self.assertIn({"name": "alignment", "value": "left", "start": 33, "end": 47}, annotations)
        self.assertIn({"name": "bold", "value": "True", "start": 33, "end": 47}, annotations)
        self.assertIn({"name": "bold", "value": "True", "start": 0, "end": 15}, annotations)

    def test_html_table_with_styles(self) -> None:
        file_name = "table_with_styles.html"
        result = self._send_request(file_name)
        table = result["content"]["tables"][0]
        self.assertEqual(table["cells"][1][0]["lines"][0]["annotations"][0], {"start": 0, "end": 6, "name": "bold", "value": "True"})
        self.assertEqual(table["cells"][1][1]["lines"][0]["annotations"][0], {"start": 0, "end": 10, "name": "italic", "value": "True"})
        self.assertEqual(table["cells"][2][0]["lines"][0]["annotations"][0], {"start": 0, "end": 10, "name": "linked_text", "value": "https://github.com/ispras/dedoc"})
        self.assertEqual(table["cells"][2][1]["lines"][0]["annotations"][0], {"start": 0, "end": 16, "name": "strike", "value": "True"})

    def test_html_font_style_attribute(self) -> None:
        file_name = "210.html"
        self._send_request(file_name)

    def test_html_newlines(self) -> None:
        file_name = "some.html"
        result = self._send_request(file_name)
        content = result["content"]["structure"]

        node = self._get_by_tree_path(content, "0.0")
        text = node["text"]
        self.assertEqual("Support", text.strip())
        self.assertEqual("header", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(content, "0.0.0")
        text = node["text"]
        self.assertIn("Technical support:", text)
        self.assertIn("Facility / Shipping / Mailing address:", text)
        self.assertIn("Grand Rapids, MI 49512-9704 USA", text)
        self.assertIn("Repair and overhaul administration: ", text)
        self.assertIn("Data services:", text)
        self.assertIn("For service repair (Part 145) returned material authorizations (RMA):", text)

    def __check_metainfo(self, metainfo: dict, actual_type: str, actual_name: str) -> None:
        self.assertEqual(metainfo["file_type"], actual_type)
        self.assertEqual(metainfo["file_name"], actual_name)

    def test_html_encoding(self) -> None:
        file_name = "53.html"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        text = content["subparagraphs"][0]["text"]
        self.assertTrue(text.startswith("\n\n"))

    def test_html_no_newline(self) -> None:
        file_name = "no_new_line.html"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        node = content["subparagraphs"][0]
        text = node["text"]
        expected_text = (
            '"I can’t bring myself to feel too sorry for Amazon or textbook publishers, given how much they tend to gouge on the prices of those books."'
        )
        self.assertEqual(expected_text, text.strip())
        italics = [text[annotation["start"]: annotation["end"]] for annotation in node["annotations"] if annotation["name"] == "italic"]
        self.assertIn("or", italics)

    def test_html_none_display(self) -> None:
        file_name = "none_display.html"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        annotations = content["subparagraphs"][0]["annotations"]
        self.assertIn({"name": "style", "value": "hidden", "start": 24, "end": 39}, annotations)
        self.assertIn({"name": "bold", "value": "True", "start": 45, "end": 49}, annotations)
