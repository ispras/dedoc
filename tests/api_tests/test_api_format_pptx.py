import os

from dedoc.data_structures import TableAnnotation
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPPTXReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "pptx")

    def test_pptx(self) -> None:
        file_name = "example.pptx"
        result = self._send_request(file_name, data=dict(structure_type="linear"))
        self.__check_content(result["content"])

    def test_ppt(self) -> None:
        file_name = "example.ppt"
        result = self._send_request(file_name, data=dict(structure_type="linear"))
        self.__check_content(result["content"])

    def test_odp(self) -> None:
        file_name = "example.odp"
        result = self._send_request(file_name, data=dict(structure_type="linear"))
        self.__check_content(result["content"])

    def test_structure_and_annotations(self) -> None:
        file_name = "test-presentation.pptx"
        result = self._send_request(file_name, data=dict(with_attachments="True"))
        structure = result["content"]["structure"]

        # Test headers
        node = self._get_by_tree_path(structure, "0.0")
        self.assertEqual("Title\n", node["text"])
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "size"]
        self.assertEqual(1, len(annotations))
        self.assertEqual(50.0, float(annotations[0]["value"]))
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "alignment"]
        self.assertEqual(1, len(annotations))
        self.assertEqual("center", annotations[0]["value"])
        node = self._get_by_tree_path(structure, "0.2")
        self.assertEqual("Title\n", node["text"])
        self.assertEqual("header", node["metadata"]["paragraph_type"])

        # Test lists
        self.assertEqual("list", self._get_by_tree_path(structure, "0.2.1")["metadata"]["paragraph_type"])
        self.assertEqual("1. first item\n", self._get_by_tree_path(structure, "0.2.1.0")["text"])
        self.assertEqual("2. second item\n", self._get_by_tree_path(structure, "0.2.1.1")["text"])
        self.assertEqual("list", self._get_by_tree_path(structure, "0.2.1.1.0")["metadata"]["paragraph_type"])
        self.assertEqual("a. subitem\n", self._get_by_tree_path(structure, "0.2.1.1.0.0")["text"])
        self.assertEqual("3. third item\n", self._get_by_tree_path(structure, "0.2.1.2")["text"])
        self.assertEqual("list", self._get_by_tree_path(structure, "0.2.1.2.0")["metadata"]["paragraph_type"])
        self.assertEqual("a. \n", self._get_by_tree_path(structure, "0.2.1.2.0.0")["text"])

        self.assertEqual("❏ first bullet item\n", self._get_by_tree_path(structure, "0.3.0.0")["text"])
        self.assertEqual("❏ second bullet item\n", self._get_by_tree_path(structure, "0.3.0.1")["text"])
        self.assertEqual("❏ subitem\n", self._get_by_tree_path(structure, "0.3.0.1.0.0")["text"])
        self.assertEqual("A. first letter item\n", self._get_by_tree_path(structure, "0.3.1.0")["text"])
        self.assertEqual("B. second letter item\n", self._get_by_tree_path(structure, "0.3.1.1")["text"])
        self.assertEqual("○ first subitem\n", self._get_by_tree_path(structure, "0.3.1.1.0.0")["text"])
        self.assertEqual("○ second subitem\n", self._get_by_tree_path(structure, "0.3.1.1.0.1")["text"])

        # Test annotations
        node = self._get_by_tree_path(structure, "0.5")
        self.assertEqual("Custom title\n", node["text"])
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "size"]
        self.assertEqual(30.0, float(annotations[0]["value"]))
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "bold"]
        self.assertEqual("True", annotations[0]["value"])
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "alignment"]
        self.assertEqual("center", annotations[0]["value"])

        node = self._get_by_tree_path(structure, "0.5.0")
        annotations = {float(annotation["value"]) for annotation in node["annotations"] if annotation["name"] == "size"}
        self.assertSetEqual({18.0, 24.0, 10.0}, annotations)
        self.assertIn({"start": 18, "end": 27, "name": "bold", "value": "True"}, node["annotations"])
        self.assertIn({"start": 28, "end": 39, "name": "italic", "value": "True"}, node["annotations"])
        self.assertIn({"start": 40, "end": 55, "name": "underlined", "value": "True"}, node["annotations"])
        self.assertIn({"start": 56, "end": 67, "name": "strike", "value": "True"}, node["annotations"])
        self.assertIn({"start": 68, "end": 79, "name": "superscript", "value": "True"}, node["annotations"])
        self.assertIn({"start": 81, "end": 90, "name": "subscript", "value": "True"}, node["annotations"])

        node = self._get_by_tree_path(structure, "0.6")
        self.assertIn({"start": 0, "end": 12, "name": "bold", "value": "True"}, node["annotations"])
        self.assertIn({"start": 0, "end": 12, "name": "italic", "value": "True"}, node["annotations"])
        self.assertIn({"start": 0, "end": 12, "name": "underlined", "value": "True"}, node["annotations"])
        self.assertIn({"start": 0, "end": 12, "name": "size", "value": "20.0"}, node["annotations"])
        self.assertIn({"start": 0, "end": 13, "name": "alignment", "value": "right"}, node["annotations"])

        # Test tables
        tables = result["content"]["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]
        node = self._get_by_tree_path(structure, "0.4")
        annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "table"]
        self.assertEqual(table["metadata"]["uid"], annotations[0]["value"])
        column_number = len(table["cells"][0])
        for table_row in table["cells"]:
            self.assertEqual(column_number, len(table_row))

        cell = table["cells"][0][0]
        self.assertEqual("Horizontally merged cells\n", cell["lines"][0]["text"])
        self.assertEqual(1, cell["rowspan"])
        self.assertEqual(2, cell["colspan"])
        self.assertEqual(False, cell["invisible"])
        cell = table["cells"][0][1]
        self.assertEqual("Horizontally merged cells\n", cell["lines"][0]["text"])
        self.assertEqual(1, cell["rowspan"])
        self.assertEqual(1, cell["colspan"])
        self.assertEqual(True, cell["invisible"])

        cell = table["cells"][1][2]
        self.assertEqual("Vertically merged cells\n", cell["lines"][0]["text"])
        self.assertEqual(2, cell["rowspan"])
        self.assertEqual(1, cell["colspan"])
        self.assertEqual(False, cell["invisible"])
        cell = table["cells"][2][2]
        self.assertEqual("Vertically merged cells\n", cell["lines"][0]["text"])
        self.assertEqual(1, cell["rowspan"])
        self.assertEqual(1, cell["colspan"])
        self.assertEqual(True, cell["invisible"])

        cell = table["cells"][2][0]
        self.assertEqual("Vertically merged cells 2\n", cell["lines"][0]["text"])
        self.assertEqual(2, cell["rowspan"])
        self.assertEqual(1, cell["colspan"])
        self.assertEqual(False, cell["invisible"])
        cell = table["cells"][3][0]
        self.assertEqual("Vertically merged cells 2\n", cell["lines"][0]["text"])
        self.assertEqual(1, cell["rowspan"])
        self.assertEqual(1, cell["colspan"])
        self.assertEqual(True, cell["invisible"])

        cell = table["cells"][3][2]
        self.assertEqual("Horizontally merged cells 2\n", cell["lines"][0]["text"])
        self.assertEqual(1, cell["rowspan"])
        self.assertEqual(3, cell["colspan"])
        self.assertEqual(False, cell["invisible"])
        cell = table["cells"][3][3]
        self.assertEqual("Horizontally merged cells 2\n", cell["lines"][0]["text"])
        self.assertEqual(1, cell["rowspan"])
        self.assertEqual(1, cell["colspan"])
        self.assertEqual(True, cell["invisible"])

        # Test attachments
        self.assertEqual(3, len(result["attachments"]))
        attachment_uids = {attachment["metadata"]["uid"] for attachment in result["attachments"]}
        node = self._get_by_tree_path(structure, "0.6")
        annotations = [annotation["value"] for annotation in node["annotations"] if annotation["name"] == "attachment"]
        self.assertIn(annotations[0], attachment_uids)
        self.assertIn(annotations[1], attachment_uids)
        node = self._get_by_tree_path(structure, "0.8.0")
        self.assertEqual("Text text\n", node["text"])
        annotations = [annotation["value"] for annotation in node["annotations"] if annotation["name"] == "attachment"]
        self.assertIn(annotations[0], attachment_uids)

    def __check_content(self, content: dict) -> None:
        subparagraphs = content["structure"]["subparagraphs"]
        self.assertEqual("A long time ago in a galaxy far far away", subparagraphs[0]["text"].strip())
        self.assertEqual("Example", subparagraphs[1]["text"].strip())
        self.assertEqual("Some author", subparagraphs[2]["text"].strip())
        self.assertEqual("This is simple table", subparagraphs[3]["text"].strip())

        table = content["tables"][0]
        self.assertListEqual(["", "Header1\n", "Header2\n", "Header3\n"], self._get_text_of_row(table["cells"][0]))
        self.assertListEqual(["Some content\n", "A\n", "B\n", "C\n"], self._get_text_of_row(table["cells"][1]))

        table_annotations = [ann for ann in subparagraphs[2]["annotations"] if ann["name"] == TableAnnotation.name]
        self.assertEqual(1, len(table_annotations))
        self.assertEqual(table_annotations[0]["value"], table["metadata"]["uid"])
