from pathlib import Path
from unittest import TestCase

import cv2

from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.metadata.page import PageMetadata
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.processors.parsing.pdf.preprocessing.orientation_classification import OrientationClassification, OrientationClassifierConfig


class TestOrientationClassification(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent.resolve() / "tests" / "data" / "scanned"
        self.processor = OrientationClassification(OrientationClassifierConfig())

    def test_orientation_classification(self) -> None:
        page_nodes = []
        for i in range(1, 9):
            file_path = str(self.data_path / f"orient_{i}.png")
            file_node = FileNode(file_path)
            image = cv2.imread(file_path)
            page_node = PageNodeWrapper.wrap(PageNode(metadata=PageMetadata(file_ref=file_node, number=i))).set_orig_image(image)
            page_nodes.append(page_node)

        result = self.processor.process(page_nodes, PdfBaseConfig())
        self.assertEqual(0, len(result.new_nodes))
        self.assertEqual(0, len(result.delete_nodes))
        self.assertEqual(8, len(result.changed_nodes))
        page2angle = {1: 90., 2: 90., 3: 270., 4: 270., 5: 180., 6: 270., 7: 180., 8: 270.}

        for result_node in result.changed_nodes:
            wrapped_node = PageNodeWrapper.wrap(result_node)
            with self.subTest(page_number=wrapped_node.metadata.number):
                self.assertIsNotNone(wrapped_node.angle)
                self.assertEqual(page2angle[wrapped_node.metadata.number], wrapped_node.angle)
