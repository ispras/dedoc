import os
from typing import List

from src.tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiAttachmentsReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "xlsx")

    def _check_attachments(self, attachments: List[dict]) -> None:
        for attachment in attachments:
            self.assertTrue(attachment["attachments"] is not None)

    def test_wo_attachments_excel(self) -> None:
        file_name = "example.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        self.assertEqual([], result['attachments'])

    def test_get_attachments_xlxs_depth_1(self) -> None:
        file_name = "example_with_images.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result['attachments']
        self._check_attachments(attachments)

    def test_get_attachments_xls_depth_1(self) -> None:
        file_name = "example_with_images.xls"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result['attachments']
        self._check_attachments(attachments)
