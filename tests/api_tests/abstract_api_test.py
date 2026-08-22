import json
import os

import requests

from dedoc.utils.utils import similarity as utils_similarity
from tests.api_tests.content_checker import ContentChecker
from tests.test_utils import check_object_refs, collect_annotation_values


class AbstractTestApiDocReader(ContentChecker):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    def _check_similarity(self, actual: str, expected: str, threshold: float = 0.8) -> None:
        if utils_similarity(actual, expected) <= threshold:
            self.assertEqual(expected, actual)

    def _check_metainfo(self, metainfo: dict, actual_type: str, actual_name: str) -> None:
        self.assertEqual(metainfo["file_type"], actual_type)
        self.assertEqual(metainfo["file_name"], actual_name)

    def _get_host(self) -> str:
        host = os.environ.get("DOC_READER_HOST", "localhost")
        return host

    def _get_port(self) -> int:
        port = int(os.environ.get("DOCREADER_PORT", "1231"))
        return port

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, file_name)

    def _send_request(self, file_name: str, data: dict = None, expected_code: int = 200) -> dict:
        """
        send file `file_name` in post request with `data` as parameters. Expects that response return code
        `expected_code`

        :param file_name: name of file (should lie  src/tests/data folder
        :param data: parameter dictionary (here you can put language for example)
        :param expected_code: expected http response code. 200 for normal request
        :return: result from json
        """
        if data is None:
            data = {}

        host = self._get_host()
        port = self._get_port()
        abs_path = self._get_abs_path(file_name)

        with open(abs_path, "rb") as file:
            files = {"file": (file_name, file)}
            r = requests.post(f"http://{host}:{port}/upload", files=files, data=data)
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

        r = requests.post(f"http://{host}:{port}/upload", data=data)

        self.assertEqual(expected_code, r.status_code)
        if expected_code != 200:
            return None

        result = json.loads(r.content.decode())
        return result

    def _test_table_refs(self, content: dict, require_one_to_one: bool = False) -> None:
        annotation_uids = collect_annotation_values(content["structure"], "table")
        table_uids = [table["metadata"]["uid"] for table in content["tables"]]
        errors = check_object_refs(table_uids, annotation_uids, require_all_linked=True, require_one_to_one=require_one_to_one, kind="table")
        self.assertEqual([], errors, "\n".join(errors))

    def _test_attach_refs(self, result: dict, require_all_linked: bool = False, require_one_to_one: bool = False) -> None:
        annotation_uids = collect_annotation_values(result["content"]["structure"], "attachment")
        attach_uids = [attachment["metadata"]["uid"] for attachment in result.get("attachments", [])]
        errors = check_object_refs(
            attach_uids, annotation_uids, require_all_linked=require_all_linked, require_one_to_one=require_one_to_one, kind="attachment"
        )
        self.assertEqual([], errors, "\n".join(errors))
