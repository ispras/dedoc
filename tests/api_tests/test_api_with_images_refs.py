from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiImageRefs(AbstractTestApiDocReader):
    def test_docx_with_images(self):
        file_name = "docx_with_images.docx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][1]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image1.png')

        image_paragraph = content["subparagraphs"][4]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image3.jpeg')

        image_paragraph = content["subparagraphs"][8]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image4.jpeg')

        image_paragraph = content["subparagraphs"][10]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image5.jpeg')
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image6.jpeg')

        image_paragraph = content["subparagraphs"][11]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image7.jpeg')

    def test_odt_with_images(self):
        file_name = "odt_with_images.odt"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][1]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image1.jpeg')

        image_paragraph = content["subparagraphs"][8]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image2.jpeg')

        image_paragraph = content["subparagraphs"][10]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image3.jpeg')

    def test_docx_with_images_from_mac(self):
        file_name = "doc_with_images.docx"
        result = self._send_request(file_name, dict(with_attachments=True, structure_type="linear"))
        content = result["content"]["structure"]

        image_paragraph = content["subparagraphs"][3]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image1.jpeg')

        image_paragraph = content["subparagraphs"][5]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image2.jpeg')

        image_paragraph = content["subparagraphs"][7]
        self.__check_image_paragraph(image_paragraph=image_paragraph, image_name='image3.png')

    def __check_image_paragraph(self, image_paragraph: dict, image_name: str):
        text = image_paragraph["text"]
        image_annotations = image_paragraph["annotations"]
        self.assertIn({'start': 0, 'end': len(text), 'name': 'attachment', 'value': image_name}, image_annotations)
