import json
import os

from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiCSVReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "json", file_name))

    def test_string(self) -> None:
        file_name = "string.json"
        result = self._send_request(file_name)["content"]["structure"]["subparagraphs"][0]
        self.assertEqual("у попа была собака", result["text"])

    def test_list(self) -> None:
        file_name = "list.json"
        result = self._send_request(file_name, data=dict(structure_type="tree"))["content"]["structure"]
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
        self.assertEqual("key1", nodes[0]["metadata"]["paragraph_type"])
        self.assertEqual("у попа была собака", nodes[0]["text"])
        self.assertEqual("key2", nodes[1]["metadata"]["paragraph_type"])
        self.assertEqual("он её любил", nodes[1]["text"])

    def test_dict_with_list(self) -> None:
        file_name = "dict_with_list.json"
        result = self._send_request(file_name, data=dict(structure_type="tree"))["content"]["structure"]
        nodes = result["subparagraphs"]
        days = [node for node in nodes if node["metadata"]["paragraph_type"] == "days"][0]
        months = [node for node in nodes if node["metadata"]["paragraph_type"] == "month"][0]
        self.assertEqual("days", days["metadata"]["paragraph_type"])
        first_list_items = months["subparagraphs"][0]["subparagraphs"]

        self.assertEqual(3, len(first_list_items))
        self.assertEqual("июнь", first_list_items[0]["text"])
        self.assertEqual("июль", first_list_items[1]["text"])
        self.assertEqual("август", first_list_items[2]["text"])

        second_list_items = days["subparagraphs"][0]["subparagraphs"]
        self.assertEqual(2, len(second_list_items))
        self.assertEqual("понедельник", second_list_items[0]["text"])
        self.assertEqual("вторник", second_list_items[1]["text"])

    def test_list_with_dict(self) -> None:
        file_name = "list_with_dict.json"
        nodes = self._send_request(file_name, data=dict(structure_type="tree"))["content"]["structure"]
        self.assertEqual("list", nodes["subparagraphs"][0]["metadata"]["paragraph_type"])

        first_list_items = nodes["subparagraphs"][0]["subparagraphs"][0]["subparagraphs"][0]["subparagraphs"][0][
            "subparagraphs"]
        self.assertEqual(3, len(first_list_items))
        self.assertEqual("июнь", first_list_items[0]["text"])
        self.assertEqual("июль", first_list_items[1]["text"])
        self.assertEqual("август", first_list_items[2]["text"])

        second_list_items = nodes["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][0]["subparagraphs"][0][
            "subparagraphs"]
        self.assertEqual(2, len(second_list_items))
        self.assertEqual("понедельник", second_list_items[0]["text"])
        self.assertEqual("вторник", second_list_items[1]["text"])

    def test_realistic(self) -> None:
        file_name = "realistic_json.json"
        result = self._send_request(file_name, data=dict(structure_type="tree"))["content"]["structure"]
        result_dict = {node["metadata"]["paragraph_type"]: node["text"] for node in result["subparagraphs"]}
        with open(self._get_abs_path(file_name)) as file:
            real_dict = json.load(file)
        self.assertEqual(len(result_dict), len(real_dict) - 1)
        self.assertEqual(real_dict["title"], result["text"])
        for k in real_dict:
            if k != "text" and k != "title":
                self.assertEqual(real_dict[k], result_dict[k])
