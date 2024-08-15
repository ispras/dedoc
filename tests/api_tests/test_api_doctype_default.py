from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDefaultStructure(AbstractTestApiDocReader):

    def test_patterns(self) -> None:
        file_name = "docx/without_numbering.docx"
        patterns = [
            {"name": "regexp", "regexp": "^глава\s\d+\.", "line_type": "глава", "level_1": 1},  # noqa
            {"name": "start_word", "start_word": "статья", "level_1": 2, "line_type": "статья"},
            {"name": "dotted_list", "level_1": 3, "line_type": "list_item"},
            {"name": "bracket_list", "level_1": 4, "level_2": 1, "line_type": "list_item"}
        ]
        result = self._send_request(file_name, {"patterns": str(patterns)})
        structure = result["content"]["structure"]

        node = self._get_by_tree_path(structure, "0.1")
        self.assertEqual(node["text"], "Глава 1. Общие положения")
        self.assertEqual(node["metadata"]["paragraph_type"], "глава")
        node = self._get_by_tree_path(structure, "0.2")
        self.assertEqual(node["text"], "Глава 2. Административные правонарушения, посягающие на права граждан и здоровье населения")
        self.assertEqual(node["metadata"]["paragraph_type"], "глава")

    def test_wrong_patterns(self) -> None:
        file_name = "docx/example.docx"
        self._send_request(file_name, {"patterns": str([{"regexp": "^глава\s\d+\.", "line_type": "глава", "level_1": 1}])}, expected_code=400)  # noqa
        self._send_request(file_name, {"patterns": str([{"name": "start_word", "line_type": "глава", "level_1": 1}])}, expected_code=400)
        self._send_request(file_name, {"patterns": str([1])}, expected_code=400)
