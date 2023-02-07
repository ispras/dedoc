import os
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiAttachmentsReader(AbstractTestApiDocReader):

    data_directory_path = AbstractTestApiDocReader.data_directory_path

    def check_pdf_1(self, pdf: dict) -> None:
        content = pdf["content"]['structure']
        self.assertEqual("Глава 543\n", content["subparagraphs"][0]["text"])
        self.assertEqual("Какой-то текст.\n", content["subparagraphs"][0]["subparagraphs"][0]["text"])
        self.assertEqual(content["subparagraphs"][0]["subparagraphs"][1]["subparagraphs"][0]['text'], '1.\n')
        self.assertEqual(content["subparagraphs"][0]["subparagraphs"][1]["subparagraphs"][1]['text'], '2.\n')
        self.assertEqual(content["subparagraphs"][0]["subparagraphs"][1]["subparagraphs"][2]['text'], '3.\n')

    def check_pdf_2(self, pdf: dict) -> None:
        content = pdf["content"]
        self.assertEqual("Пример документа\n", content['structure']['subparagraphs'][0]["text"])

    def _check_attachments(self, attachments: List[dict]) -> None:
        for attachment in attachments:
            self.assertTrue(attachment["attachments"] is not None)

    def test_wo_attachments_excel(self) -> None:
        file_name = "xlsx/example.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        self.assertEqual([], result['attachments'])

    def test_get_attachments_xlxs_depth_1(self) -> None:
        file_name = "xlsx/example_with_images.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result['attachments']
        self._check_attachments(attachments)

    def test_get_attachments_xls_depth_1(self) -> None:
        file_name = "xlsx/example_with_images.xls"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result['attachments']
        self._check_attachments(attachments)

    def test_get_attachments_pdf_depth_1(self) -> None:
        file_name = "with_attachments/example_with_attachments_depth_1.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, pdf_with_text_layer="tabby"))

        attachments = result["attachments"]

        self.assertEqual(attachments[0]["metadata"]["file_name"], "header_test.pdf")
        self.assertEqual(attachments[1]["metadata"]["file_name"], "example_with_table4.jpg")
        self.assertEqual(attachments[2]["metadata"]["file_name"], "header_test.pdf")
        self.assertEqual(attachments[3]["metadata"]["file_name"], "attachment.txt")
        self.assertEqual(attachments[4]["metadata"]["file_type"], "application/json")

    def test_attachments_pmi_document(self):
        file_name = "pdf_with_text_layer/Document635.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, pdf_with_text_layer="tabby"))

        attachments = result["attachments"]

        self.assertEqual(attachments[0]["metadata"]["file_type"], "application/json")
        self.assertEqual(attachments[1]["metadata"]["file_type"], "application/json")