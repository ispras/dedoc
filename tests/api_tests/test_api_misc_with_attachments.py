import base64
import json
import os
from tempfile import TemporaryDirectory
from typing import List

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiAttachmentsReader(AbstractTestApiDocReader):

    data_directory_path = AbstractTestApiDocReader.data_directory_path

    def _check_attachments(self, attachments: List[dict]) -> None:
        for attachment in attachments:
            self.assertTrue(attachment["attachments"] is not None)

    def test_wo_attachments_excel(self) -> None:
        file_name = "xlsx/example.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        self.assertEqual([], result["attachments"])

    def test_get_attachments_xlxs_depth_1(self) -> None:
        file_name = "xlsx/example_with_images.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result["attachments"]
        self._check_attachments(attachments)

    def test_get_attachments_xls_depth_1(self) -> None:
        file_name = "xlsx/example_with_images.xls"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result["attachments"]
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

    def test_attachments_pmi_document(self) -> None:
        file_name = "pdf_with_text_layer/Document635.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, pdf_with_text_layer="tabby"))

        attachments = result["attachments"]

        self.assertEqual(attachments[0]["metadata"]["file_type"], "application/json")
        self.assertEqual(attachments[1]["metadata"]["file_type"], "application/json")

    def test_need_content_analysis(self) -> None:
        file_name = "pdf_with_text_layer/Document635.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, need_content_analysis=False, pdf_with_text_layer="tabby"))

        attachments = result["attachments"]
        self.assertEqual(len(attachments[0]["content"]["structure"]["subparagraphs"]), 0)
        self.assertEqual(len(attachments[1]["content"]["structure"]["subparagraphs"]), 0)

        result = self._send_request(file_name, dict(with_attachments=True, need_content_analysis=True, pdf_with_text_layer="tabby"))
        attachments = result["attachments"]
        self.assertGreater(len(attachments[0]["content"]["structure"]["subparagraphs"]), 0)
        self.assertGreater(len(attachments[1]["content"]["structure"]["subparagraphs"]), 0)

    def test_get_without_attachments(self) -> None:
        file_name = "with_attachments/example_with_attachments_depth_1.pdf"
        result = self._send_request(file_name, dict(with_attachments=False))
        self.assertEqual([], result["attachments"])

    def test_json_attachments(self) -> None:
        file_name = "json/with_html.json"
        parameters = dict()
        parameters["with_attachments"] = True
        parameters["html_fields"] = json.dumps([["title"], ["body"], ["example"], ["deep_key1", "deep_key2", "deep_key3"]])

        result = self._send_request(file_name, parameters)
        attachments = result["attachments"]

        self.assertEqual(len(attachments), 4)

    def test_json_invalid_html_fields(self) -> None:
        file_name = "json/with_html.json"
        parameters = dict()
        parameters["with_attachments"] = True
        parameters["html_fields"] = json.dumps([
            ["title"], ["example"], ["another_field"], ["test"], ["lists"], ["log"], ["text"], ["deep_key1", "deep_key2", "deep_key3"]
        ])

        result = self._send_request(file_name, parameters)
        attachments = result["attachments"]

        self.assertEqual(len(attachments), 4)

    def test_json_with_html_fields_with_scripts(self) -> None:
        file_name = "json/example2.json"
        parameters = dict(with_attachments=True, html_fields=json.dumps([["text"]]), need_content_analysis=True)

        result = self._send_request(file_name, parameters)
        attachments = result["attachments"]

        self.assertEqual(len(attachments), 1)

        attachment = attachments[0]["content"]["structure"]["subparagraphs"]
        self.assertEqual(len(attachment), 3)
        self.assertEqual(attachment[1]["text"], "\n\nWeb Content Viewer\n")
        self.assertEqual(attachment[2]["text"].strip(), "Let us know how we can help")

    def test_json_with_bad_style_in_html(self) -> None:
        file_name = "json/0001-p1.json"
        parameters = dict()
        parameters["with_attachments"] = True
        parameters["html_fields"] = json.dumps([["news_link"], ["publication_title"], ["publication_date"], ["publication_author"], ["text_publication"]])

        result = self._send_request(file_name, parameters)
        attachments = result["attachments"]

        self.assertEqual(len(attachments), 5)

    def test_docx_attachments(self) -> None:
        file_name = "with_attachments/with_attachments_0.docx"
        result = self._send_request(file_name, dict(with_attachments=True, need_content_analysis=True))

        attachments = result["attachments"]
        names = [attachment["metadata"]["file_name"] for attachment in attachments]
        self.assertIn("arch_with_attachs.zip", names)
        self.assertIn("VVP_global_table.pdf", names)
        self.assertIn("lorem.txt", names)
        self.assertIn("books.csv", names)

        arch = [attachment for attachment in attachments if attachment["metadata"]["file_name"] == "arch_with_attachs.zip"][0]
        self.assertEqual(len(arch["attachments"]), 4)

        txt = [attachment for attachment in attachments if attachment["metadata"]["file_name"] == "lorem.txt"][0]

        self.assertIn("Adipisicing est non minim aute reprehenderit incididunt magna ad consectetur ad occaecat anim voluptate culpa fugiat",
                      txt["content"]["structure"]["subparagraphs"][0]["text"], )

    def test_docx_images_base64(self) -> None:
        metadata = self.__check_base64(True)
        base64_encode = metadata["base64_encode"]
        file_name = metadata["file_name"]
        with TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, file_name)
            with open(path, "wb") as file_out:
                file_out.write(base64.decodebytes(base64_encode.encode()))
            result_english = self._send_request(file_name=path, data={})
            self._check_english_doc(result_english)

    def test_docx_images_no_base64(self) -> None:
        metadata = self.__check_base64(False)
        self.assertNotIn("base64_encode", metadata)

    def __check_base64(self, with_base64: bool) -> dict:
        file_name = "pdf_auto/mixed_pdf.pdf"
        data = dict(with_attachments=True, pdf_with_text_layer="true")
        if with_base64:
            data["return_base64"] = True
        result = self._send_request(file_name=file_name, data=data)
        self.assertNotIn("base64_encode", result["metadata"])
        attachments = result["attachments"]
        self.assertEqual(1, len(attachments))
        attachment = attachments[0]
        # check that attachment on cloud and looks fine
        metadata = attachment["metadata"]
        return metadata

    def test_attachments_recursion(self) -> None:
        file_name = "with_attachments/with_attachments_0.docx"

        result = self._send_request(file_name=file_name, data=dict(with_attachments=True, need_content_analysis=True, recursion_deep_attachments=0))
        self.assertEqual(0, len(result["attachments"]))

        result = self._send_request(file_name=file_name, data=dict(with_attachments=True, need_content_analysis=True, recursion_deep_attachments=1))
        self.assertLess(0, len(result["attachments"]))
        self.assertEqual(0, len(result["attachments"][1]["attachments"]))

        result = self._send_request(file_name=file_name, data=dict(with_attachments=True, need_content_analysis=True, recursion_deep_attachments=2))
        self.assertLess(0, len(result["attachments"]))
        self.assertLess(0, len(result["attachments"][1]["attachments"]))
