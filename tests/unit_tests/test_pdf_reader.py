import os
import shutil
import unittest
from tempfile import TemporaryDirectory
from typing import List
import cv2
import re

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from dedoc.readers.pdf_reader.pdf_image_reader.scan_rotator import ScanRotator
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_with_text_reader import PdfWithTextReader
from tests.test_utils import get_test_config


class TestPDFReader(unittest.TestCase):
    checkpoint_path = get_test_config()["resources_path"]
    config = get_test_config()
    orientation_classifier = ColumnsOrientationClassifier(on_gpu=False, checkpoint_path=checkpoint_path, delete_lines=True, config=config)

    def _split_lines_on_pages(self, lines: List[LineWithMeta]) -> List[List[str]]:
        pages = set(map(lambda x: x.metadata.page_id, lines))
        lines_by_page = [[line.line for line in lines if line.metadata.page_id == page_id] for page_id in pages]

        return lines_by_page

    def test_scan_rotator(self) -> None:
        scan_rotator = ScanRotator(config=get_test_config())
        imgs_path = [f'../data/scan_rotator/rotated_{i}.jpg' for i in range(1, 5)]
        angles = [0.061732858955328755, -0.017535263190370427, 0.12228411148417097, 0]

        for i in range(len(imgs_path)):
            path = os.path.join(os.path.dirname(__file__), imgs_path[i])
            image = cv2.imread(path)
            _, orientation = self.orientation_classifier.predict(image)
            angle_predict = self.orientation_classifier.classes[2 + orientation]
            rotated, angle = scan_rotator.auto_rotate(image, angle_predict)
            self.assertAlmostEqual(angle, angles[i], delta=8)

    def test_scan_orientation(self) -> None:
        scan_rotator = ScanRotator(config=get_test_config())
        imgs_path = [f'../data/scanned/orient_{i}.png'for i in range(1, 5)]
        angles = [90.0, 90.0, 270.0, 270.0]
        max_delta = 10.0
        for i in range(len(imgs_path)):
            path = os.path.join(os.path.dirname(__file__), imgs_path[i])
            image = cv2.imread(path)
            _, angle_predict = self.orientation_classifier.predict(image)
            rotated, angle = scan_rotator.auto_rotate(image, angle_predict)
            self.assertTrue(abs(angle - angles[i]) < max_delta)

    def test_header_footer_search(self) -> None:
        config = get_test_config()
        any_doc_reader = PdfWithTextReader(config=config)
        with TemporaryDirectory() as tmpdir:
            filename = "prospectus.pdf"
            path = os.path.join(os.path.dirname(__file__), "../data/pdf_with_text_layer", filename)
            shutil.copy(path, os.path.join(tmpdir, filename))
            result = any_doc_reader.read(os.path.join(tmpdir, filename),
                                         document_type=None,
                                         parameters={"need_header_footer_analysis": "True", "need_pdf_table_analysis": "False"})

        lines_by_page = self._split_lines_on_pages(result.lines)

        headers = [lines[0] for lines in lines_by_page if lines[0] == 'Richelieu Bond \n']
        footers = [lines[-1] for lines in lines_by_page if re.match(r"^\s*-( )*[0-9]+( )*-\s*$", lines[-1])]

        self.assertEqual(len(headers), 0)
        self.assertEqual(len(footers), 0)

    def test_header_footer_search_2(self) -> None:
        config = get_test_config()
        any_doc_reader = PdfWithTextReader(config=config)
        with TemporaryDirectory() as tmpdir:
            filename = "with_changed_header_footer.pdf"
            path = os.path.join(os.path.dirname(__file__), "../data/pdf_with_text_layer", filename)
            shutil.copy(path, os.path.join(tmpdir, filename))
            result = any_doc_reader.read(os.path.join(tmpdir, filename),
                                         document_type=None,
                                         parameters={"need_header_footer_analysis": "True", "need_pdf_table_analysis": "False"})

        lines_by_page = self._split_lines_on_pages(result.lines)

        headers = [lines[0] for lines in lines_by_page
                   if lines[0] == 'Richelieu Bond \n']
        footers = [lines[-1] for lines in lines_by_page
                   if re.match(r"^\s*-( )*[0-9]+( )*-\s*$", lines[-1])]

        self.assertEqual(len(headers), 0)
        self.assertEqual(len(footers), 0)

    def test_header_footer_search_3(self) -> None:
        config = get_test_config()
        any_doc_reader = PdfWithTextReader(config=config)
        with TemporaryDirectory() as tmpdir:
            filename = "with_header_footer_2.pdf"
            path = os.path.join(os.path.dirname(__file__), "../data/pdf_with_text_layer", filename)
            shutil.copy(path, os.path.join(tmpdir, filename))
            result = any_doc_reader.read(os.path.join(tmpdir, filename),
                                         document_type=None,
                                         parameters={"need_header_footer_analysis": "True", "need_pdf_table_analysis": "False"})

        lines_by_page = self._split_lines_on_pages(result.lines)

        headers = [lines[0] for lines in lines_by_page
                   if lines[0] == 'QUEST MANAGEMENT, SICAV\n']
        footers = [lines[-1] for lines in lines_by_page
                   if re.match(r"^\s*[0-9]\s*$", lines[-1])]

        self.assertEqual(len(headers), 1)
        self.assertEqual(len(footers), 0)

    def test_long_list_pdf(self) -> None:
        config = get_test_config()
        any_doc_reader = PdfImageReader(config=config)
        path = os.path.join(os.path.dirname(__file__), "../data/scanned/doc_with_long_list.pdf")
        result = any_doc_reader.read(path, document_type=None, parameters={"need_pdf_table_analysis": "False"})
        list_elements = result.lines[1:]
        self.assertEqual(list_elements[0].line.lower().strip(), "1. январь")
        self.assertEqual(list_elements[1].line.lower().strip(), "2. февраль")
        self.assertEqual(list_elements[2].line.lower().strip(), "3. март")
        self.assertEqual(list_elements[3].line.lower().strip(), "4. апрель")
        self.assertEqual(list_elements[4].line.lower().strip(), "5. май")
        self.assertEqual(list_elements[5].line.lower().strip(), "6. июнь")
        self.assertEqual(list_elements[6].line.lower().strip(), "7. июль")
        self.assertEqual(list_elements[7].line.lower().strip(), "8. август")
        self.assertEqual(list_elements[8].line.lower().strip(),
                         "9. сентябрь в сентябре, в сентябре много листьев на земле желтые и красные! все такие")
        self.assertEqual(list_elements[9].line.lower().strip(), "разные!")
        self.assertEqual(list_elements[10].line.lower().strip(), "10. октябрь")
        self.assertEqual(list_elements[11].line.lower().strip(), "11. ноябрь")
        self.assertEqual(list_elements[12].line.lower().strip(), "12. декабрь")

    def test_pdf_text_layer(self) -> None:
        config = get_test_config()
        any_doc_reader = PdfWithTextReader(config=config)
        path = os.path.join(os.path.dirname(__file__), "../data/pdf_with_text_layer/english_doc.pdf")
        result = any_doc_reader.read(path, document_type=None, parameters={})
        for line in result.lines:
            # check that annotations not duplicated
            annotations = line.annotations
            annotations_set = {(a.name, a.value, a.start, a.end) for a in annotations}
            self.assertEqual(len(annotations_set), len(annotations))
