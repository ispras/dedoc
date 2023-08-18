import json
import os
from json import JSONDecodeError

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiJSONReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.abspath(os.path.join(self.data_directory_path, "json", file_name))

    def test_string(self) -> None:
        file_name = "string.json"
        result = self._send_request(file_name)["content"]["structure"]["subparagraphs"][0]
        self.assertEqual("у попа была собака", result["text"])

    def test_list(self) -> None:
        file_name = "list.json"
        result = self._send_request(file_name)["content"]["structure"]
        list_node = result["subparagraphs"][0]
        self.assertEqual("list", list_node["metadata"]["paragraph_type"])
        list_items = list_node["subparagraphs"]
        self.assertEqual(2, len(list_items))
        self.assertEqual("list_item", list_items[0]["metadata"]["paragraph_type"])
        self.assertEqual("у попа была собака", list_items[0]["text"])
        self.assertEqual("list_item", list_items[1]["metadata"]["paragraph_type"])
        self.assertEqual("он её любил", list_items[1]["text"])

    def test_dict(self) -> None:
        file_name = "dict.json"
        result = self._send_request(file_name)["content"]["structure"]
        nodes = result["subparagraphs"]
        self.assertEqual("key", nodes[0]["metadata"]["paragraph_type"])
        self.assertEqual("у попа была собака", nodes[0]["subparagraphs"][0]["text"])
        self.assertEqual("key", nodes[1]["metadata"]["paragraph_type"])
        self.assertEqual("он её любил", nodes[1]["subparagraphs"][0]["text"])

    def test_dict_with_list(self) -> None:
        file_name = "dict_with_list.json"
        result = self._send_request(file_name)["content"]["structure"]
        first_list_items = result["subparagraphs"][0]["subparagraphs"][0]["subparagraphs"]
        second_list_items = result["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"]
        first_list_items, second_list_items = sorted([first_list_items, second_list_items], key=lambda l: -len(l))

        nodes = result["subparagraphs"][1]["subparagraphs"]
        self.assertEqual("list", nodes[0]["metadata"]["paragraph_type"])
        self.assertEqual(3, len(first_list_items))
        self.assertEqual("июнь", first_list_items[0]["text"])
        self.assertEqual("июль", first_list_items[1]["text"])
        self.assertEqual("август", first_list_items[2]["text"])

        self.assertEqual(2, len(second_list_items))
        self.assertEqual("понедельник", second_list_items[0]["text"])
        self.assertEqual("вторник", second_list_items[1]["text"])

    def test_list_with_dict(self) -> None:
        file_name = "list_with_dict.json"
        result = self._send_request(file_name)["content"]["structure"]
        self._check_tree_sanity(tree=result)
        self.assertEqual("month", self._get_by_tree_path(result, "0.0.0.0")["text"])
        self.assertEqual("июнь", self._get_by_tree_path(result, "0.0.0.0.0.0")["text"])
        self.assertEqual("июль", self._get_by_tree_path(result, "0.0.0.0.0.1")["text"])
        self.assertEqual("август", self._get_by_tree_path(result, "0.0.0.0.0.2")["text"])

        self.assertEqual("days", self._get_by_tree_path(result, "0.1.0.0")["text"])
        self.assertEqual("понедельник", self._get_by_tree_path(result, "0.1.0.0.0.0")["text"])
        self.assertEqual("вторник", self._get_by_tree_path(result, "0.1.0.0.0.1")["text"])

    def test_realistic(self) -> None:
        file_name = "realistic_json.json"
        result = self._send_request(file_name)["content"]["structure"]["subparagraphs"]
        result_dict = [(node["metadata"]["paragraph_type"], node["text"]) for node in result]
        with open(self._get_abs_path(file_name)) as file:
            real_dict = json.load(file)
        self.assertEqual(len(result_dict), len(real_dict))

    def test_broken(self) -> None:
        file_name = "broken.json"
        self._send_request(file_name, expected_code=415)

    def test_json_attachments2(self) -> None:
        file_name = "test2.json"
        data = {"html_fields": '[["e"], ["f"]]', "with_attachments": "True", "return_base64": "true"}
        self._send_request(file_name, expected_code=200, data=data)

    def test_json_null(self) -> None:
        file_name = "test_null.json"
        result = self._send_request(file_name, expected_code=200)
        paragraphs = result["content"]["structure"]["subparagraphs"]
        self.assertEqual(paragraphs[0]["text"], "author")
        self.assertEqual(paragraphs[0]["metadata"]["paragraph_type"], "key")
        self.assertEqual(paragraphs[0]["subparagraphs"][0]["text"], "James Fontanella-Khan")
        self.assertEqual(paragraphs[0]["subparagraphs"][0]["metadata"]["paragraph_type"], "raw_text")

        self.assertEqual(paragraphs[1]["text"], "category")
        self.assertEqual(paragraphs[1]["metadata"]["paragraph_type"], "key")
        self.assertEqual(len(paragraphs[1]["subparagraphs"]), 0)

        self.assertEqual(paragraphs[5]["text"], "tags")
        self.assertEqual(paragraphs[5]["metadata"]["paragraph_type"], "key")
        self.assertEqual(len(paragraphs[5]["subparagraphs"]), 0)
        pass

    def test_json_broken_parameters(self) -> None:
        file_name = "test2.json"
        data = {"html_fields": "[[ef]]", "with_attachments": "True", "return_base64": "true"}
        with self.assertRaises(JSONDecodeError):
            json.loads(data["html_fields"])
        self._send_request(file_name, expected_code=400, data=data)
