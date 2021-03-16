from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiImageRefs(AbstractTestApiDocReader):
    def test_docx_with_images(self):
        file_name = "docx_with_images.docx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][1]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image1.png'} in image_annotations)

        image_paragraph = content["subparagraphs"][4]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image3.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][8]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image4.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][10]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image5.jpeg'} in image_annotations)
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image6.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][11]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image7.jpeg'} in image_annotations)

    def test_odt_with_images(self):
        file_name = "odt_with_images.odt"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][1]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image1.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][8]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image2.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][10]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image3.jpeg'} in image_annotations)

    def test_docx_with_images_from_mac(self):
        file_name = "doc_with_images.docx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][3]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image1.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][5]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image2.jpeg'} in image_annotations)

        image_paragraph = content["subparagraphs"][7]
        image_annotations = image_paragraph["annotations"]
        self.assertTrue({'start': -1, 'end': -1, 'name': 'attachment', 'value': 'image3.png'} in image_annotations)
