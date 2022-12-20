import os
import unittest


from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.utils.image_utils import supported_image_types


class TestApiPdfReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "scanned", file_name)

    def __check_example_file(self, result: dict) -> None:
        content = result["content"]["structure"]["subparagraphs"]
        self._check_similarity("Пример документа", content[0]["text"].strip())
        annotations = content[0]["annotations"]
        self.assertIn(BoldAnnotation.name, [annotation["name"] for annotation in annotations])
        self.assertIn(SpacingAnnotation.name, [annotation["name"] for annotation in annotations])
        self._check_similarity("одну строчку.\nКакие то определения",
                               content[1]["subparagraphs"][0]["text"])
        self._check_similarity("Статья 1", content[1]["subparagraphs"][1]["text"])
        self._check_similarity("Статья 2", content[1]["subparagraphs"][2]["text"])
        self._check_similarity("1.2.1 Поясним за непонятное",
                               content[1]["subparagraphs"][2]["subparagraphs"][1]["subparagraphs"][0]["text"])

    def __check_metainfo(self, metainfo: dict, actual_type: str, actual_name: str) -> None:
        self.assertEqual(metainfo['file_type'], actual_type)
        self.assertEqual(metainfo['file_name'], actual_name)

    def test_pdf(self) -> None:
        file_name = "example.pdf"
        result = self._send_request(file_name,
                                    data=dict(with_attachments=True, document_type="", pdf_with_text_layer="true"))
        self.__check_example_file(result)
        self.__check_metainfo(result['metadata'], 'application/pdf', file_name)
        self.assertEqual([], result['attachments'])

    # TODO include when add table processing
    @unittest.skip
    def test_djvu(self) -> None:
        file_name = "example_with_table7.djvu"
        result = self._send_request(file_name, dict(document_type=""))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self.assertEqual('2. Срок поставки в течении 70 дней с момента внесения авансового платежа.\n',
                         self._get_by_tree_path(tree, "0.2.1")['text'])
        self.assertEqual("3. Срок изготовления не ранее 2018г.\n", self._get_by_tree_path(tree, "0.2.2")['text'])

        self.__check_metainfo(result['metadata'], 'image/vnd.djvu', file_name)

    # TODO include when add table processing
    @unittest.skip
    def test_djvu_2(self) -> None:
        file_name = "example_with_table9.djvu"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        self._check_tree_sanity(content)
        self.assertEqual("1. Предмет закупки, источник финансирования :\n",
                         self._get_by_tree_path(content, "0.1.0")["text"])
        self.assertEqual("2.   Место выполнения Работ:\n",
                         self._get_by_tree_path(content, "0.1.1")["text"])

        self.__check_metainfo(result['metadata'], 'image/vnd.djvu', file_name)

    def test_broken_djvu(self) -> None:
        file_name = "broken.djvu"
        _ = self._send_request(file_name, expected_code=415)

    @unittest.skip("TODO")
    def test_header_pdf(self) -> None:
        file_name = "header_test.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="true"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self._check_similarity("Глава 543", self._get_by_tree_path(tree, "0.0")["text"])
        self._check_similarity("Какой-то текст.", self._get_by_tree_path(tree, "0.0.0")["text"])

        self._check_similarity("1. Текстового", self._get_by_tree_path(tree, "0.0.1.0")["text"])

        self._check_similarity("2. Текстового", self._get_by_tree_path(tree, "0.0.1.1")["text"])

        self._check_similarity("3. Еще текстового", self._get_by_tree_path(tree, "0.0.1.2")["text"])

        self._check_similarity("4. Пам", self._get_by_tree_path(tree, "0.0.1.3")["text"])

        self._check_similarity("4.1. авп", self._get_by_tree_path(tree, "0.0.1.3.0.0")["text"])

        self._check_similarity("4.2. текстового", self._get_by_tree_path(tree, "0.0.1.3.0.1")["text"])

        self._check_similarity("4.3. п", self._get_by_tree_path(tree, "0.0.1.3.0.2")["text"])

        self._check_similarity("4.4.", self._get_by_tree_path(tree, "0.0.1.3.0.3")["text"])

        self._check_similarity("4.5.", self._get_by_tree_path(tree, "0.0.1.3.0.4")["text"])

        self._check_similarity("4.6.", self._get_by_tree_path(tree, "0.0.1.3.0.5")["text"])

        self.__check_metainfo(result['metadata'], 'application/pdf', file_name)

    def test_images(self) -> None:
        formats = [
            '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.ppm', '.pnm', '.pgm',
            '.pbm', '.webp', '.pcx', '.eps', '.sgi', '.hdr', '.pic', '.sr', '.ras',
            '.dib', '.jpe', '.jfif', '.j2k'
        ]

        for image_format in formats:
            self.assertIn(image_format, supported_image_types)
            file_name = "example"
            result = self._send_request(file_name + image_format)
            self.__check_example_file(result)

    def test_image_metadata(self) -> None:
        file_name = "orient_3.png"
        result = self._send_request(file_name)
        exif = result["metadata"]["other_fields"]
        self.assertEqual(exif["exif_image_width"], 1654)
        self.assertEqual(exif["exif_image_height"], 2338)

    def test_on_ocr_conf_threshold(self) -> None:
        result = self._send_request("with_trash.jpg", data=dict(structure_type="tree"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        # check, that handwritten text was filtered
        self.assertIn("№ выдан _, дата выдачи\nт. код подразделения зарегистрированный по адресу:\n",
                      tree['subparagraphs'][2]['text'])

    @unittest.skip
    def test_rotated_image(self) -> None:
        result = self._send_request("orient_1.png", data=dict(need_pdf_table_analysis="false"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        self._check_similarity(tree['subparagraphs'][0]['text'], 'Приложение к Положению о порядке\n'
                                                                 'формирования, ведения и утверждения\n'
                                                                 'ведомственных перечней государственных услуг\n'
                                                                 'и работ, оказываемых и выполняемых\n'
                                                                 'государственными учреждениями Калужской\n'
                                                                 'области\n')
