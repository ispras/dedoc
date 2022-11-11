import json
import os
import requests

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApi(AbstractTestApiDocReader):

    def __get_version(self) -> str:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION"))
        with open(path) as file:
            version = file.read().strip()
            return version

    def test_bin_file(self) -> None:
        file_name = "file.bin"
        result = self._send_request(file_name, expected_code=415)
        result = json.loads(result)
        self.assertIn("dedoc_version", result)
        self.assertEqual(file_name, result["file_name"])
        self.assertIn("metadata", result)

    def test_send_wo_file(self) -> None:
        self._send_request_wo_file(expected_code=400)

    def test_version(self) -> None:
        version = self.__get_version()
        r = requests.get("http://{host}:{port}/version".format(host=self._get_host(), port=self._get_port()))
        self.assertEqual(version, r.text.strip())

    def test_version_parsed_file(self) -> None:
        version = self.__get_version()
        result = self._send_request("csvs/books.csv")
        self.assertEqual(version, result["version"].strip())

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
