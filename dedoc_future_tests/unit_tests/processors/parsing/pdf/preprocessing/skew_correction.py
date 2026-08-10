from pathlib import Path
from unittest import TestCase

import cv2
import numpy as np
import pytesseract
from tdm import TalismanDocumentFactory

from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.metadata.page import PageMetadata
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.processors.parsing.pdf.preprocessing.skew_correction import SkewCorrection


class TestSkewCorrection(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent.resolve() / "tests" / "data" / "skew_corrector"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = SkewCorrection()

    def test_skew_correction(self) -> None:
        structure = {}
        for i in range(1, 5):
            file_path = str(self.data_path / f"rotated_{i}.jpg")
            file_node = FileNode(file_path)
            image = cv2.imread(file_path)
            page_node = PageNodeWrapper.wrap(PageNode(metadata=PageMetadata(file_ref=file_node, number=i))).set_orig_image(image)
            structure[file_node] = [page_node]

        document = self.document.with_structure(structure, update=True)
        result = self.processor.process(document, list(document.get_nodes(PageNode)), PdfBaseConfig())

        self.assertEqual(0, len(result.structure))
        self.assertEqual(4, len(result.nodes))

        page2angle = {1: 3., 2: -1., 3: 7., 4: 0.}

        for result_node in result.nodes:
            wrapped_node = PageNodeWrapper.wrap(result_node)
            self.assertIsNotNone(wrapped_node.angle, f"Page {wrapped_node.metadata.number}")
            self.assertEqual(page2angle[wrapped_node.metadata.number], wrapped_node.angle, f"Page {wrapped_node.metadata.number}")

    def test_zero_angle(self) -> None:
        structure = {}
        for i in range(1, 6):
            file_path = str(self.data_path / f"short_lines-{i}.png")
            file_node = FileNode(file_path)
            image = cv2.imread(file_path)
            page_node = PageNodeWrapper.wrap(PageNode(metadata=PageMetadata(file_ref=file_node, number=i))).set_orig_image(image)
            structure[file_node] = [page_node]

        document = self.document.with_structure(structure, update=True)
        result = self.processor.process(document, list(document.get_nodes(PageNode)), PdfBaseConfig())

        self.assertEqual(0, len(result.structure))
        self.assertEqual(5, len(result.nodes))

        for result_node in result.nodes:
            wrapped_node = PageNodeWrapper.wrap(result_node)
            self.assertIsNotNone(wrapped_node.angle, f"Page {wrapped_node.metadata.number}")
            self.assertEqual(0, wrapped_node.angle, f"Page {wrapped_node.metadata.number}")
            self.assertIsNotNone(wrapped_node.image, f"Page {wrapped_node.metadata.number}")
            self.assertIsNotNone(wrapped_node.orig_image, f"Page {wrapped_node.metadata.number}")
            self.assertEqual(wrapped_node.image.shape, wrapped_node.orig_image.shape, f"Page {wrapped_node.metadata.number}")
            self.assertTrue(np.array_equal(wrapped_node.image, wrapped_node.orig_image), f"Page {wrapped_node.metadata.number}")

    def test_correct_angle(self) -> None:
        file_path = str(self.data_path / "rotated_3.jpg")
        file_node = FileNode(file_path)
        image = cv2.imread(file_path)
        page_node = PageNodeWrapper.wrap(PageNode(metadata=PageMetadata(file_ref=file_node, number=0))).set_orig_image(image)
        result = self.processor.process(self.document, [page_node], PdfBaseConfig())

        self.assertEqual(0, len(result.structure))
        self.assertEqual(1, len(result.nodes))

        result_node = PageNodeWrapper.wrap(result.nodes[0])
        text = pytesseract.image_to_string(result_node.image, lang="rus", config="--psm 3")
        self.assertIn("«Упражнения с решениями»", text)
        text = pytesseract.image_to_string(result_node.orig_image, lang="rus", config="--psm 3")
        self.assertNotIn("«Упражнения с решениями»", text)
