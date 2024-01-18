import os
import unittest

import cv2
from dedocutils.data_structures import BBox

from dedoc.data_structures import BoldAnnotation
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.data_classes.word_with_bbox import WordWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.font_type_classifier import FontTypeClassifier


class TestFontClassifier(unittest.TestCase):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "scanned"))
    classifier = FontTypeClassifier()

    def get_page(self) -> PageWithBBox:
        image = cv2.imread(os.path.join(self.data_directory_path, "example.png"))

        bboxes = [
            TextWithBBox(
                bbox=BBox(79, 86, 214, 21), page_num=0, line_num=0,
                words=[WordWithBBox(text="Пример", bbox=BBox(79, 86, 89, 21)), WordWithBBox(text="документа", bbox=BBox(175, 90, 118, 17))]
            ),
            TextWithBBox(
                bbox=BBox(79, 113, 627, 20), page_num=0, line_num=0,
                words=[
                    WordWithBBox(text="Глава", bbox=BBox(79, 113, 58, 15)), WordWithBBox(text="1", bbox=BBox(144, 113, 9, 15)),
                    WordWithBBox(text="c", bbox=BBox(160, 117, 8, 11)), WordWithBBox(text="таким", bbox=BBox(175, 117, 62, 11)),
                    WordWithBBox(text="длинным", bbox=BBox(243, 118, 94, 14)), WordWithBBox(text="названием", bbox=BBox(344, 117, 105, 11)),
                    WordWithBBox(text="которое", bbox=BBox(456, 117, 77, 16)), WordWithBBox(text="даже", bbox=BBox(539, 117, 48, 15)),
                    WordWithBBox(text="не", bbox=BBox(594, 117, 21, 11)), WordWithBBox(text="влазит", bbox=BBox(622, 117, 67, 11)),
                    WordWithBBox(text="в", bbox=BBox(695, 118, 11, 10))
                ]
            ),
            TextWithBBox(
                bbox=BBox(80, 142, 132, 16), page_num=0, line_num=0,
                words=[WordWithBBox(text="одну", bbox=BBox(80, 142, 44, 16)), WordWithBBox(text="строчку.", bbox=BBox(131, 142, 81, 16))]
            ),
            TextWithBBox(
                bbox=BBox(80, 163, 154, 15), page_num=0, line_num=0,
                words=[
                    WordWithBBox(text="Какие", bbox=BBox(80, 163, 41, 11)), WordWithBBox(text="то", bbox=BBox(126, 166, 14, 8)),
                    WordWithBBox(text="определения", bbox=BBox(146, 166, 88, 12))
                ]
            ),
            TextWithBBox(
                bbox=BBox(79, 182, 65, 11), page_num=0, line_num=0,
                words=[WordWithBBox(text="Статья", bbox=BBox(79, 182, 53, 11)), WordWithBBox(text="1", bbox=BBox(138, 182, 6, 11))]
            ),
            TextWithBBox(bbox=BBox(79, 201, 166, 15), page_num=0, line_num=0, words=[WordWithBBox(text="опрделения", bbox=BBox(164, 204, 81, 12))]),
            TextWithBBox(
                bbox=BBox(79, 220, 66, 11), page_num=0, line_num=0,
                words=[WordWithBBox(text="Статья", bbox=BBox(79, 220, 53, 11)), WordWithBBox(text="2", bbox=BBox(138, 220, 7, 11))]
            ),
            TextWithBBox(
                bbox=BBox(79, 239, 124, 14), page_num=0, line_num=0,
                words=[WordWithBBox(text="Дадим", bbox=BBox(79, 239, 46, 14)), WordWithBBox(text="пояснения", bbox=BBox(130, 242, 73, 8))]
            ),
            TextWithBBox(
                bbox=BBox(81, 259, 203, 11), page_num=0, line_num=0,
                words=[
                    WordWithBBox(text="1.2.1", bbox=BBox(81, 259, 30, 11)), WordWithBBox(text="Поясним", bbox=BBox(117, 259, 62, 11)),
                    WordWithBBox(text="за", bbox=BBox(185, 262, 12, 8)), WordWithBBox(text="непонятное", bbox=BBox(203, 262, 81, 8))
                ]
            ),
            TextWithBBox(
                bbox=BBox(81, 278, 191, 11), page_num=0, line_num=0,
                words=[
                    WordWithBBox(text="1.2.2", bbox=BBox(81, 278, 34, 11)), WordWithBBox(text="Поясним", bbox=BBox(121, 278, 62, 11)),
                    WordWithBBox(text="за", bbox=BBox(189, 281, 13, 8)), WordWithBBox(text="понятное", bbox=BBox(207, 281, 65, 8))
                ]
            ),
            TextWithBBox(
                bbox=BBox(129, 297, 171, 15), page_num=0, line_num=0,
                words=[
                    WordWithBBox(text="а)", bbox=BBox(129, 297, 11, 14)), WordWithBBox(text="это", bbox=BBox(146, 300, 21, 8)),
                    WordWithBBox(text="даже", bbox=BBox(172, 300, 34, 11)), WordWithBBox(text="ежу", bbox=BBox(211, 300, 26, 12)),
                    WordWithBBox(text="понятно", bbox=BBox(243, 300, 57, 8))
                ]
            ),
            TextWithBBox(
                bbox=BBox(129, 315, 153, 16), page_num=0, line_num=0,
                words=[
                    WordWithBBox(text="б)", bbox=BBox(129, 315, 12, 15)), WordWithBBox(text="это", bbox=BBox(147, 319, 21, 8)),
                    WordWithBBox(text="ежу", bbox=BBox(174, 319, 26, 12)), WordWithBBox(text="не", bbox=BBox(205, 319, 15, 8)),
                    WordWithBBox(text="понятно", bbox=BBox(225, 319, 57, 8))
                ]
            ),
            TextWithBBox(bbox=BBox(81, 335, 30, 11), page_num=0, line_num=0, words=[WordWithBBox(text="1.23", bbox=BBox(81, 335, 30, 11))]),
        ]

        return PageWithBBox(image=image, bboxes=bboxes, page_num=0)

    def test_bold_classification(self) -> None:
        page = self.get_page()
        self.classifier.predict_annotations(page)

        for bbox in page.bboxes[:3]:
            self.assertIn(BoldAnnotation.name, [annotation.name for annotation in bbox.annotations])

        for bbox in page.bboxes[3:]:
            self.assertNotIn(BoldAnnotation.name, [annotation.name for annotation in bbox.annotations])
