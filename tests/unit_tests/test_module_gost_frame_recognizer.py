import os.path
import unittest
from typing import Optional

import cv2
import numpy as np

import dedoc.utils.parameter_utils as param_utils
from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_auto_reader import PdfAutoReader
from dedoc.readers.pdf_reader.pdf_base_reader import ParametersForParseDoc
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.gost_frame_recognizer import GOSTFrameRecognizer
from tests.test_utils import get_test_config


class TestGOSTFrameRecognizer(unittest.TestCase):

    gost_frame_recognizer = GOSTFrameRecognizer(config=get_test_config())
    test_data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "tables"))
    pdf_image_reader = PdfImageReader(config=get_test_config())
    pdf_auto_reader = PdfAutoReader(config=get_test_config())

    def _get_params_for_parse(self, parameters: Optional[dict], file_path: Optional[str]) -> ParametersForParseDoc:
        parameters = parameters if parameters else {}
        file_path = file_path if file_path else ""
        params_for_parse = ParametersForParseDoc(
            language=param_utils.get_param_language(parameters),
            orient_analysis_cells=param_utils.get_param_orient_analysis_cells(parameters),
            orient_cell_angle=param_utils.get_param_orient_cell_angle(parameters),
            is_one_column_document=param_utils.get_param_is_one_column_document(parameters),
            document_orientation=param_utils.get_param_document_orientation(parameters),
            need_header_footers_analysis=param_utils.get_param_need_header_footers_analysis(parameters),
            need_pdf_table_analysis=param_utils.get_param_need_pdf_table_analysis(parameters),
            first_page=0,
            last_page=0,
            need_binarization=param_utils.get_param_need_binarization(parameters),
            table_type=param_utils.get_param_table_type(parameters),
            with_attachments=param_utils.get_param_with_attachments(parameters),
            attachments_dir=param_utils.get_param_attachments_dir(parameters, file_path),
            need_content_analysis=param_utils.get_param_need_content_analysis(parameters),
            need_gost_frame_analysis=param_utils.get_param_need_gost_frame_analysis(parameters),
            pdf_with_txt_layer=param_utils.get_param_pdf_with_txt_layer(parameters)
        )
        return params_for_parse

    def test_gost_frame_recognition(self) -> None:
        image_names = [
            "gost_frame_1.jpg", "gost_frame_2.png", "gost_frame_3.jpg", "example_with_table6.png", "example_with_table5.png", "example_with_table3.png"
        ]
        gt = [True, True, True, False, False, False]
        for index, image_name in enumerate(image_names):
            path_image = os.path.join(self.test_data_folder, image_name)
            image = cv2.imread(path_image)
            result_image, result_bbox = self.gost_frame_recognizer.rec_and_clean_frame(image)
            self.assertEqual(not np.array_equal(result_image, image), gt[index])  # check if we cut something from original image or not

    def test_not_gost_frame(self) -> None:
        path_image = os.path.join(self.test_data_folder, "not_gost_frame.jpg")
        image = cv2.imread(path_image)
        result_image, result_bbox = self.gost_frame_recognizer.rec_and_clean_frame(image)
        self.assertTrue(abs(result_bbox.x_top_left - 26) < 10)
        self.assertTrue(abs(result_bbox.y_top_left - 26) < 10)
        self.assertTrue(abs(result_bbox.width - 722) < 10)
        self.assertTrue(abs(result_bbox.height - 969) < 10)

    def test_coordinates_shift(self) -> None:
        file_path = os.path.join(self.test_data_folder, "gost_frame_2.png")
        parameters = {"need_gost_frame_analysis": "True"}
        params_for_parse = self._get_params_for_parse(parameters=parameters, file_path=file_path)
        result = self.pdf_image_reader._parse_document(path=file_path, parameters=params_for_parse)
        self.assertTrue(len(result[0]) > 0)
        self.assertTrue(abs(result[0][0].location.bbox.x_top_left - 365) < 10)
        self.assertTrue(abs(result[0][0].location.bbox.y_top_left - 37) < 10)
        self.assertTrue(abs(result[0][1].location.bbox.x_top_left - 84) < 10)
        self.assertTrue(abs(result[0][1].location.bbox.y_top_left - 580) < 10)
        self.assertTrue(len(result[1]) > 0)
        self.assertTrue(abs(result[1][0].location.bbox.x_top_left - 81) < 10)
        self.assertTrue(abs(result[1][0].location.bbox.y_top_left - 49) < 10)

    def test_pdf_auto_reader(self) -> None:
        file_path = os.path.join(self.test_data_folder, "gost_frame_2.png")
        parameters = {"need_gost_frame_analysis": "True"}
        result = self.pdf_auto_reader.read(file_path=file_path, parameters=parameters)
        self.assertTrue(len(result.tables) == 1)
        self.assertEqual(result.tables[0].cells[0][1].get_text(), "Колонка 2")
        self.assertEqual(result.tables[0].cells[0][2].get_text(), "Колонка 3")
        self.assertEqual(len(result.tables[0].cells), 22)
        self.assertTrue("Название таблицы (продолжение)" in result.lines[0].line)
