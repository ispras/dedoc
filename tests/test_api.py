import os

from tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    def test_text(self) -> None:
        file_name = "doc_001.txt"
        result = self._send_request(os.path.join("txt", file_name), data=dict(structure_type="tree"))
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')
        indentation = [annotation["value"] for annotation in content["subparagraphs"][1]["annotations"]
                       if annotation["name"] == "indentation"]
        self.assertEqual(1, len(indentation))
        self.assertEqual(211 * 5, int(indentation[0]))
        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    def test_bin_file(self) -> None:
        self._send_request("file.bin", expected_code=415)
