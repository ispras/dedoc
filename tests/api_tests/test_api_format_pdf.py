import os

from dedoc.data_structures import BBoxAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.confidence_annotation import ConfidenceAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.utils import supported_image_types
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "scanned", file_name)

    def __check_example_file(self, result: dict) -> None:
        content = result["content"]["structure"]["subparagraphs"]
        self._check_similarity("Пример документа", content[0]["text"].strip().split("\n")[0])
        annotations = content[0]["annotations"]
        annotation_names = {annotation["name"] for annotation in annotations}
        self.assertIn(BoldAnnotation.name, annotation_names)
        self.assertIn(SpacingAnnotation.name, annotation_names)
        self.assertIn(ConfidenceAnnotation.name, annotation_names)
        self.assertIn(BBoxAnnotation.name, annotation_names)
        self._check_similarity("1.2.1 Поясним за непонятное", content[3]["subparagraphs"][0]["text"])

    def __check_metainfo(self, metainfo: dict, actual_type: str, actual_name: str) -> None:
        self.assertEqual(metainfo["file_type"], actual_type)
        self.assertEqual(metainfo["file_name"], actual_name)

    def test_pdf(self) -> None:
        file_name = "example.pdf"
        result = self._send_request(file_name, data=dict(with_attachments=True, document_type="", pdf_with_text_layer="false"))
        self.__check_example_file(result)
        self.__check_metainfo(result["metadata"], "application/pdf", file_name)
        self.assertEqual([], result["attachments"])

    def test_djvu(self) -> None:
        file_name = "example_with_table7.djvu"
        result = self._send_request(file_name, dict(document_type=""))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self.assertEqual("2. Срок поставки в течении 70 дней с момента внесения авансового платежа.\n", self._get_by_tree_path(tree, "0.2.1")["text"])
        self.assertEqual("3. Срок изготовления не ранее 2018г.\n", self._get_by_tree_path(tree, "0.2.2")["text"])

        self.__check_metainfo(result["metadata"], "image/vnd.djvu", file_name)

    def test_djvu_2(self) -> None:
        file_name = "example_with_table9.djvu"
        result = self._send_request(file_name)
        content = result["content"]["structure"]
        self._check_tree_sanity(content)
        self.assertEqual("1. Предмет закупки, источник финансирования :\n", self._get_by_tree_path(content, "0.1.0")["text"])
        self.assertEqual("2.   Место выполнения Работ:\n", self._get_by_tree_path(content, "0.1.1")["text"])

        self.__check_metainfo(result["metadata"], "image/vnd.djvu", file_name)

    def test_broken_djvu(self) -> None:
        file_name = "broken.djvu"
        _ = self._send_request(file_name, expected_code=415)

    def test_header_pdf(self) -> None:
        file_name = "header_test.pdf"
        result = self._send_request(file_name, data=dict(pdf_with_text_layer="true"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self._check_similarity("Глава 543\nКакой-то текст.", self._get_by_tree_path(tree, "0.0")["text"])
        self._check_similarity("1. Текстового", self._get_by_tree_path(tree, "0.1.0")["text"])
        self._check_similarity("2. Текстового", self._get_by_tree_path(tree, "0.1.1")["text"])
        self._check_similarity("3. Еще текстового", self._get_by_tree_path(tree, "0.1.2")["text"])
        self._check_similarity("4. Пам", self._get_by_tree_path(tree, "0.1.3")["text"])
        self._check_similarity("4.1. авп", self._get_by_tree_path(tree, "0.1.3.0.0")["text"])
        self._check_similarity("4.2. текстового", self._get_by_tree_path(tree, "0.1.3.0.1")["text"])
        self._check_similarity("4.3. п", self._get_by_tree_path(tree, "0.1.3.0.2")["text"])
        self._check_similarity("4.4. п", self._get_by_tree_path(tree, "0.1.3.0.3")["text"])
        self._check_similarity("4.5. п", self._get_by_tree_path(tree, "0.1.3.0.4")["text"])
        self._check_similarity("4.6. п", self._get_by_tree_path(tree, "0.1.3.0.5")["text"])

        self.__check_metainfo(result["metadata"], "application/pdf", file_name)

    def test_images(self) -> None:
        formats = [
            ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".ppm", ".pnm", ".pgm",
            ".pbm", ".webp", ".pcx", ".eps", ".sgi", ".hdr", ".pic", ".sr", ".ras",
            ".dib", ".jpe", ".jfif", ".j2k"
        ]

        for image_format in formats:
            self.assertIn(image_format, supported_image_types)
            file_name = "example"
            result = self._send_request(file_name + image_format)
            self.__check_example_file(result)

    def test_image_metadata(self) -> None:
        file_name = "orient_3.png"
        result = self._send_request(file_name)
        self.assertEqual(result["metadata"]["exif_image_width"], 1654)
        self.assertEqual(result["metadata"]["exif_image_height"], 2338)
        self.assertIn("rotated_page_angles", result["metadata"])

    def test_image_binarization(self) -> None:
        result = self._send_request("01_МФО_Наклон.jpg", data=dict(need_binarization="true"))

        self.assertIn("ЦЕНТРАЛЬНЫЙ БАНК РОССИЙСКОЙ ФЕДЕРАЦИИ\n{БАНК РОССИИ)\nСВИДЕТЕЛЬСТВО\nО ВНЕСЕНИИ СВЕДЕНИЙ О ЮРИДИЧЕСКОМ ЛИЦЕ\n"
                      "В ГОСУДАРСТВЕННЫЙ РЕЕСТР МИКРОФИНАНСОВЫХ ОРГАНИЗАЦИЙ", result["content"]["structure"]["subparagraphs"][0]["text"])
        self.assertIn("Е.И Курицына\n(расшифровка подлиси", result["content"]["structure"]["subparagraphs"][1]["text"])

    def test_on_ocr_conf_threshold(self) -> None:
        result = self._send_request("with_trash.jpg", data=dict(structure_type="tree"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        # check, that handwritten text was filtered
        self._check_similarity("ФИО  года рождения, паспорт: серия \n№ выдан _, дата выдачи\nт. код подразделения зарегистрированный по адресу:\n \n",
                               tree["subparagraphs"][3]["text"])

    def test_rotated_image(self) -> None:
        result = self._send_request("orient_1.png", data=dict(need_pdf_table_analysis="false"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        self._check_similarity(tree["subparagraphs"][0]["text"], "Приложение к Положению о порядке\n"
                                                                 "формирования, ведения и утверждения\n"
                                                                 "ведомственных перечней государственных услуг\n"
                                                                 "и работ, оказываемых и выполняемых\n"
                                                                 "государственными учреждениями Калужской\n"
                                                                 "области\n")

    def test_pdf_with_only_mp_table(self) -> None:
        file_name = os.path.join("..", "tables", "multipage_table.pdf")
        result = self._send_request(file_name)

        table_refs = [ann["value"] for ann in result["content"]["structure"]["subparagraphs"][0]["annotations"] if ann["name"] == "table"]

        self.assertTrue(len(result["content"]["tables"]), len(table_refs))
        for table in result["content"]["tables"]:
            self.assertTrue(table["metadata"]["uid"] in table_refs)

    def test_pdf_with_some_tables(self) -> None:
        file_name = os.path.join("..", "pdf_with_text_layer", "VVP_6_tables.pdf")
        result = self._send_request(file_name, data={"pdf_with_text_layer": "true"})
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self._test_table_refs(result["content"])

        # checks indentations
        par = self._get_by_tree_path(tree, "0.4.0.0")
        annotations = par["annotations"]
        self.assertIn({"end": 170, "value": "600", "name": "indentation", "start": 0}, annotations)
        self.assertIn("Методика расчета ВВП по доходам характеризуется суммой национального\n", par["text"])

    def test_pdf_with_only_table(self) -> None:
        file_name = os.path.join("..", "pdf_with_text_layer", "VVP_global_table.pdf")
        result = self._send_request(file_name)

        self.assertEqual(result["content"]["tables"][0]["metadata"]["uid"], result["content"]["structure"]["subparagraphs"][0]["annotations"][0]["value"])

    def test_2_columns(self) -> None:
        file_name = os.path.join("..", "scanned", "example_2_columns.png")
        result = self._send_request(file_name)
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self.assertEqual(797, len(self._get_by_tree_path(tree, "0.0")["text"]))

    def test_document_orientation(self) -> None:
        file_name = "orient_3.png"
        result = self._send_request(file_name, data=dict(document_orientation="auto"))
        tree = result["content"]["structure"]
        self._check_similarity(tree["subparagraphs"][0]["text"], "Приложение к постановлению\n"
                                                                 "Губернатора Камчатского края\n"
                                                                 "0729.12.2014 № 168\n"
                                                                 '"БУРЫЙ МЕДВЕДЬ\n'
                                                                 "{вид охотничьих ресурсов)\n")

    def test_bold_annotation(self) -> None:
        file_name = "bold_font.png"
        result = self._send_request(file_name)
        tree = result["content"]["structure"]

        node = tree["subparagraphs"][0]
        bold_annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "bold" and annotation["value"] == "True"]
        self.assertEqual(len(bold_annotations), 2)
        bold_annotations = sorted(bold_annotations, key=lambda x: x["start"])
        self.assertEqual((bold_annotations[0]["start"], bold_annotations[0]["end"]), (8, 12))
        self.assertEqual((bold_annotations[1]["start"], bold_annotations[1]["end"]), (29, 33))

        node = tree["subparagraphs"][1]
        bold_annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "bold" and annotation["value"] == "True"]
        self.assertEqual(len(bold_annotations), 0)

        node = tree["subparagraphs"][2]
        bold_annotations = [annotation for annotation in node["annotations"] if annotation["name"] == "bold" and annotation["value"] == "True"]
        self.assertEqual(len(bold_annotations), 1)
        self.assertEqual((bold_annotations[0]["start"], bold_annotations[0]["end"]), (0, len(node["text"].strip())))
