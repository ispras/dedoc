import os
import unittest

import cv2
from dedocutils.data_structures import BBox

from dedoc.data_structures import BoldAnnotation
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.font_type_classifier import FontTypeClassifier


class TestFontClassifier(unittest.TestCase):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "scanned"))
    classifier = FontTypeClassifier()

    def get_page(self) -> PageWithBBox:
        image = cv2.imread(os.path.join(self.data_directory_path, "example.png"))

        bboxes = [
            TextWithBBox(bbox=BBox(79, 86, 214, 21), page_num=0, text="Пример документа", line_num=0),
            TextWithBBox(bbox=BBox(79, 113, 627, 20), page_num=0, text="Глава 1 с таким длинным названием которое даже не влазит в", line_num=0),
            TextWithBBox(bbox=BBox(80, 142, 132, 16), page_num=0, text="одну строчку.", line_num=0),
            TextWithBBox(bbox=BBox(80, 163, 154, 15), page_num=0, text="Какие то определения", line_num=0),
            TextWithBBox(bbox=BBox(79, 182, 65, 11), page_num=0, text="Статья 1", line_num=0),
            TextWithBBox(bbox=BBox(79, 201, 166, 15), page_num=0, text="опрделения", line_num=0),
            TextWithBBox(bbox=BBox(79, 220, 66, 11), page_num=0, text="Статья 2", line_num=0),
            TextWithBBox(bbox=BBox(79, 239, 124, 14), page_num=0, text="Дадим пояснения", line_num=0),
            TextWithBBox(bbox=BBox(81, 259, 203, 11), page_num=0, text="1.2.1 Поясним за непонятное", line_num=0),
            TextWithBBox(bbox=BBox(81, 278, 191, 11), page_num=0, text="1.2.2. Поясним за понятное", line_num=0),
            TextWithBBox(bbox=BBox(129, 297, 171, 15), page_num=0, text="а) это даже ежу понятно", line_num=0),
            TextWithBBox(bbox=BBox(129, 315, 153, 16), page_num=0, text="6) это ежу не понятно", line_num=0),
            TextWithBBox(bbox=BBox(81, 335, 30, 11), page_num=0, text="123", line_num=0),
        ]

        return PageWithBBox(image=image, bboxes=bboxes, page_num=0)

    def test_bold_classification(self) -> None:
        page = self.get_page()
        self.classifier.predict_annotations(page)

        for bbox in page.bboxes[:3]:
            self.assertIn(BoldAnnotation.name, [annotation.name for annotation in bbox.annotations])

        for bbox in page.bboxes[3:]:
            self.assertNotIn(BoldAnnotation.name, [annotation.name for annotation in bbox.annotations])
