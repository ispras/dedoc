import os

import Levenshtein

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfBrokenEncodingReader(AbstractTestApiDocReader):
    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_with_text_layer", file_name)

    def test_text_extraction(self) -> None:
        file_name = "mongolo.pdf"
        orig_path = "../data/txt/mongolo.txt"
        result = self._send_request(file_name, dict(pdf_with_text_layer="bad_encoding_reader"))
        tree = result["content"]["structure"]
        text1 = self._get_by_tree_path(tree, "0.0")["text"]
        text2 = self._get_by_tree_path(tree, "0.1.0")["text"]
        text3 = self._get_by_tree_path(tree, "0.1.1")["text"]
        text4 = self._get_by_tree_path(tree, "0.1.2")["text"]
        text5 = '\n'.join(self._get_by_tree_path(tree, "0.1.2.0")["text"].split('\n')[:3])

        fulltext = text1 + text2 + text3 + text4 + text5
        with open(orig_path, encoding="utf8", mode="r") as txt:
            accuracy = Levenshtein.ratio(txt.read(), fulltext)
            self.assertTrue(accuracy > 0.7)
