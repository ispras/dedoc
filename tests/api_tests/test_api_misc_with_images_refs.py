import os

from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiImageRefs(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "with_attachments")

    def test_docx_with_images(self) -> None:
        file_name = "docx_with_images.docx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        attachments_name2uid = {attachment["metadata"]["file_name"]: attachment["metadata"]["uid"] for attachment in result["attachments"]}
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][0]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image1.png"])

        image_paragraph = content["subparagraphs"][2]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image2.jpeg"])
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image3.jpeg"])

        image_paragraph = content["subparagraphs"][5]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image4.jpeg"])

        image_paragraph = content["subparagraphs"][6]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image5.jpeg"])
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image6.jpeg"])
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image7.jpeg"])

    def test_odt_with_images(self) -> None:
        file_name = "odt_with_images.odt"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        attachments_name2uid = {attachment["metadata"]["file_name"]: attachment["metadata"]["uid"] for attachment in result["attachments"]}
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][0]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image1.jpeg"])

        image_paragraph = content["subparagraphs"][7]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image2.jpeg"])

        image_paragraph = content["subparagraphs"][8]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image3.jpeg"])

    def test_docx_with_images_from_mac(self) -> None:
        file_name = "doc_with_images.docx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        attachments_name2uid = {attachment["metadata"]["file_name"]: attachment["metadata"]["uid"] for attachment in result["attachments"]}
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][2]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image1.jpeg"])

        image_paragraph = content["subparagraphs"][3]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image2.jpeg"])

        image_paragraph = content["subparagraphs"][5]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_uid=attachments_name2uid["image3.png"])

    def test_pdf_pdfminer_images_refs(self) -> None:
        file_name = "with_attachments_1.docx.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear", pdf_with_text_layer="true"))
        structure = result["content"]["structure"]

        attachment_uids = {attachment["metadata"]["uid"] for attachment in result["attachments"]}
        self.assertEqual(len(attachment_uids), 3)

        attach_annotation = structure["subparagraphs"][0]["annotations"][-1]
        self.assertEqual(attach_annotation["name"], "attachment")
        self.assertIn(attach_annotation["value"], attachment_uids)

        attach_annotation = structure["subparagraphs"][2]["annotations"][-2]
        self.assertEqual(attach_annotation["name"], "attachment")
        self.assertIn(attach_annotation["value"], attachment_uids)

        attach_annotation = structure["subparagraphs"][2]["annotations"][-1]
        self.assertEqual(attach_annotation["name"], "attachment")
        self.assertIn(attach_annotation["value"], attachment_uids)

    def test_pdf_tabby_images_refs(self) -> None:
        file_name = "with_attachments_1.docx.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear", pdf_with_text_layer="tabby"))
        structure = result["content"]["structure"]

        attachment_uids = {attachment["metadata"]["uid"] for attachment in result["attachments"]}
        self.assertEqual(len(attachment_uids), 3)

        attach_annotation = structure["subparagraphs"][2]["annotations"][-1]
        self.assertEqual(attach_annotation["name"], "attachment")
        self.assertIn(attach_annotation["value"], attachment_uids)

        attach_annotation = structure["subparagraphs"][4]["annotations"][-2]
        self.assertEqual(attach_annotation["name"], "attachment")
        self.assertIn(attach_annotation["value"], attachment_uids)

        attach_annotation = structure["subparagraphs"][4]["annotations"][-1]
        self.assertEqual(attach_annotation["name"], "attachment")
        self.assertIn(attach_annotation["value"], attachment_uids)

    def test_pptx_images_refs(self) -> None:
        file_name = "with_attachments_1.pptx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))

        attachment_uids = {attachment["metadata"]["uid"] for attachment in result["attachments"]}
        self.assertEqual(len(attachment_uids), 5)

        subparagraphs = result["content"]["structure"]["subparagraphs"]
        attach_annotations = [ann for ann in subparagraphs[1]["annotations"] if ann["name"] == AttachAnnotation.name]
        self.assertEqual(len(attach_annotations), 1)
        self.assertIn(attach_annotations[0]["value"], attachment_uids)

        attach_annotations = [ann for ann in subparagraphs[3]["annotations"] if ann["name"] == AttachAnnotation.name]
        self.assertEqual(len(attach_annotations), 1)
        self.assertIn(attach_annotations[0]["value"], attachment_uids)

    def test_pdf_article_images_refs(self) -> None:
        file_name = "../pdf_with_text_layer/article.pdf"
        result = self._send_request(file_name, dict(with_attachments=True, document_type="article", structure_type="linear"))

        attachment_uids = {attachment["metadata"]["uid"] for attachment in result["attachments"]}
        self.assertEqual(len(attachment_uids), 18)

        attach_annotations_uids = set()
        for subparagraph in result["content"]["structure"]["subparagraphs"]:
            for annotation in subparagraph["annotations"]:
                if annotation["name"] == AttachAnnotation.name:
                    attach_annotations_uids.add(annotation["value"])

        self.assertTrue(attach_annotations_uids)
        self.assertTrue(attach_annotations_uids.issubset(attachment_uids))

    def __check_image_paragraph(self, image_paragraph: dict, image_uid: str) -> None:
        text = image_paragraph["text"]
        image_annotations = image_paragraph["annotations"]
        self.assertIn({"start": 0, "end": len(text), "name": "attachment", "value": image_uid}, image_annotations)
