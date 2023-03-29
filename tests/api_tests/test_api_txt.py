import os
import unittest

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from tests.test_utils import get_by_tree_path


class TestApiTxtReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "txt")

    def test_txt_file(self) -> None:
        file_name = "Pr_2013.02.18_21.txt"
        _ = self._send_request(file_name)

    def test_text(self) -> None:
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    @unittest.skip("due to tag analysis added")
    def test_text_pretty_json(self) -> None:
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data={"structure_type": "tree", "return_format": "pretty_json"})
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    @unittest.skip("due to tag analysis added")
    def test_text_bad_return_format(self) -> None:
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data={"structure_type": "tree", "return_format": "broken"})
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    def test_text2(self) -> None:
        file_name = "pr_17.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        self.assertIn("УТВЕРЖДЕНЫ", get_by_tree_path(content, "0.0")["text"])
        self.assertIn("1. Настоящие Требования разработаны в соответствии с Федеральным законом",
                      get_by_tree_path(content, "0.1.0")["text"])

    def test_special_symbols(self) -> None:
        file_name = "special_symbol.txt"
        result = self._send_request(file_name, data={"structure_type": "tree", "encoding": "utf-8"})
        content = result["content"]["structure"]
        with open(self._get_abs_path(file_name)) as file_in:
            self.assertEqual(file_in.read(), content["subparagraphs"][0]["text"])

    @unittest.skip("due to tag analysis added")
    def test_paragraphs(self) -> None:
        file_name = "football.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]["subparagraphs"]
        self.__check_football(content)

    def test_large_file(self) -> None:
        file_name = "large_text.txt.gz"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]["subparagraphs"][0]["text"]
        for line_id, line in enumerate(content.split("\n")):
            if line.strip() != "":
                self.assertEqual("Line number {:09d}".format(line_id), line)

    @unittest.skip("due to tag analysis added")
    def test_paragraphs_gz(self) -> None:
        file_name = "football.txt.gz"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]["subparagraphs"]
        self.__check_football(content)

    def __check_football(self, content: dict) -> None:
        self.assertEqual(4, len(content))
        node = content[0]
        self.assertTrue(node["text"].startswith("    Association football, more commonly known as simply"))
        self.assertTrue(node["text"].endswith("The team with the higher number of goals wins the game.\n\n"))
        annotations = node["annotations"]
        self.assertIn({'name': 'spacing', 'value': '50', 'start': 0, 'end': 546}, annotations)
        node = content[1]
        self.assertTrue(node["text"].startswith("  Football is played in accordance with a set of rules known"))
        self.assertTrue(node["text"].strip().endswith("the coin toss prior to kick-off or penalty kicks."))
        annotations = node["annotations"]
        self.assertIn({'name': 'spacing', 'value': '100', 'start': 0, 'end': 163}, annotations)
        node = content[2]
        self.assertTrue(node["text"].startswith("    Football is governed internationally by the International"))
        self.assertTrue(node["text"].endswith("the 2019 FIFA Women's World Cup in France.\n\n"))
        annotations = node["annotations"]
        self.assertIn({'name': 'spacing', 'value': '400', 'start': 0, 'end': 164}, annotations)
        self.assertIn({'name': 'spacing', 'value': '50', 'start': 164, 'end': 1068}, annotations)
        self.assertTrue(content[3]["text"].startswith("    The most prestigious competitions in European club"))
        self.assertTrue(content[3]["text"].endswith("cost in excess of £600 million/€763 million/US$1.185 billion.\n"))
