import os

import Levenshtein

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfBrokenEncodingReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_with_text_layer", file_name)

    def test_bad_encoding(self) -> None:
        file_name = "mongolo.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="bad_encoding"))
        tree = result["content"]["structure"]

        text_list = []
        for node_id in ("0.0", "0.1", "0.2", "0.3", "0.4.0", "0.4.1", "0.4.2"):
            text_list.append(self._get_by_tree_path(tree, node_id)["text"])
        text_list.append("\n".join(self._get_by_tree_path(tree, "0.4.2.0")["text"].split("\n")[:3]))

        with open(os.path.join(self.data_directory_path, "txt", "mongolo.txt"), encoding="utf8", mode="r") as txt:
            accuracy = Levenshtein.ratio(txt.read(), "".join(text_list))
            self.assertTrue(accuracy > 0.7)
