import json
import os
import unittest

import requests


class AbstractTestApiDocReader(unittest.TestCase):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    def _check_metainfo(self, metainfo: dict, actual_type: str, actual_name: str) -> None:
        self.assertEqual(metainfo['file_type'], actual_type)
        self.assertEqual(metainfo['file_name'], actual_name)

    def _get_host(self) -> str:
        host = os.environ.get('DOC_READER_HOST', 'localhost')
        return host

    def _get_port(self) -> int:
        port = int(os.environ.get('DOCREADER_PORT', '1231'))
        return port

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, file_name)

    def _send_request(self, file_name: str, data: dict = None, expected_code: int = 200) -> dict:
        """
        send file `file_name` in post request with `data` as parameters. Expects that response return code
        `expected_code`

        :param file_name: name of file (should lie  dedoc/tests/data folder
        :param data: parameter dictionary (here you can put language for example)
        :param expected_code: expected http response code. 200 for normal request
        :return: result from json
        """
        if data is None:
            data = {}

        host = self._get_host()
        port = self._get_port()
        abs_path = self._get_abs_path(file_name)

        with open(abs_path, 'rb') as file:
            files = {'file': (file_name, file)}
            r = requests.post("http://{host}:{port}/upload".format(host=host, port=port), files=files, data=data)
            self.assertEqual(expected_code, r.status_code)
            if expected_code != 200:
                return r.content.decode()
            if "return_format" in data and data["return_format"] in ("html", "tree"):
                return r.content.decode()
            else:
                return json.loads(r.content.decode())

    def _send_request_wo_file(self, data: dict = None, expected_code: int = 200) -> dict:
        host = self._get_host()
        port = self._get_port()

        if data is None:
            data = {}

        r = requests.post("http://{host}:{port}/upload".format(host=host, port=port), data=data)

        self.assertEqual(expected_code, r.status_code)
        if expected_code != 200:
            return None

        result = json.loads(r.content.decode())
        return result
