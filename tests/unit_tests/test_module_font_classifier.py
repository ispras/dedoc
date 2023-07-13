import os
import unittest

import cv2

from dedoc.data_structures.bbox import BBox
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.font_type_classifier import FontTypeClassifier
from tests.test_utils import get_test_config


class TestFontClassifier(unittest.TestCase):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "scanned"))
    path_model = os.path.abspath(os.path.join(get_test_config()["resources_path"], "font_classifier.pth"))
    classifier = FontTypeClassifier(path_model)

    def get_page_with_bbox(self, filename) -> PageWithBBox:
        image = cv2.imread(os.path.join(self.data_directory_path, filename))

        bbox_1 = TextWithBBox(bbox=BBox(10, 20, 11, 23), page_num=0, text="str", line_num=0)
        bbox_2 = TextWithBBox(bbox=BBox(20, 30, 11, 23), page_num=0, text="rts", line_num=1)
        bboxes = [bbox_1, bbox_2]

        return PageWithBBox(image=image, bboxes=bboxes, page_num=0)

    def test_page_with_bbox_converted_to_tensor(self) -> None:
        """
        Tests font classifier output tensor shape correctness
        """
        page = self.get_page_with_bbox(filename="orient_1.png")
        tensor = FontTypeClassifier._page2tensor(page=page)
        bbox_num, channels, height, width = tensor.shape
        self.assertEqual(2, bbox_num)
        self.assertEqual(3, channels)
        self.assertEqual(15, height)
        self.assertEqual(300, width)

    def test_get_model_predictions(self) -> None:
        page = self.get_page_with_bbox(filename="orient_1.png")
        predictions = self.classifier._get_model_predictions(page)
        self.assertEqual(predictions.shape[0], 2)
        self.assertEqual(len(predictions.shape), 2)
