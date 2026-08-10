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
from dedoc_future.processors.parsing.pdf.preprocessing.binarization import Binarizer, BinarizerConfig


class TestBinarizer(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent.resolve() / "tests" / "data"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = Binarizer(BinarizerConfig())

    def test_image(self) -> None:
        file_path = self.data_path / "scanned" / "01_МФО_Наклон.jpg"
        file_node = FileNode(str(file_path))
        image = cv2.imread(str(file_path))
        page_node = PageNodeWrapper.wrap(PageNode(metadata=PageMetadata(file_ref=file_node, number=0))).set_orig_image(image)
        result = self.processor.process(self.document, [page_node], PdfBaseConfig())

        self.assertEqual(0, len(result.structure))
        self.assertEqual(1, len(result.nodes))
        binarized_page_node = PageNodeWrapper.wrap(result.nodes[0])
        self.assertIsNotNone(binarized_page_node.image)
        self.assertIsNotNone(binarized_page_node.orig_image)
        self.assertEqual(binarized_page_node.image.shape, binarized_page_node.orig_image.shape)
        self.assertFalse(np.array_equal(binarized_page_node.image, binarized_page_node.orig_image))

        text = pytesseract.image_to_string(binarized_page_node.image, lang="rus", config="--psm 3")
        self.assertIn("ЦЕНТРАЛЬНЫЙ БАНК РОССИЙСКОЙ ФЕДЕРАЦИИ", text)
