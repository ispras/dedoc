from pathlib import Path
from unittest import TestCase

import cv2
from tdm import TalismanDocumentFactory

from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.metadata.page import PageMetadata
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.processors.parsing.pdf.preprocessing.orientation_classification import OrientationClassification, OrientationClassifierConfig


class TestOrientationClassification(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent.resolve() / "tests" / "data" / "scanned"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = OrientationClassification(OrientationClassifierConfig())

    def test_orientation_classification(self) -> None:
        structure = {}
        for i in range(1, 9):
            file_path = str(self.data_path / f"orient_{i}.png")
            file_node = FileNode(file_path)
            image = cv2.imread(file_path)
            page_node = PageNodeWrapper.wrap(PageNode(metadata=PageMetadata(file_ref=file_node, number=i))).set_orig_image(image)
            structure[file_node] = [page_node]

        document = self.document.with_structure(structure, update=True)
        result = self.processor.process(document, list(document.get_nodes(PageNode)), PdfBaseConfig())

        self.assertEqual(0, len(result.structure))
        self.assertEqual(8, len(result.nodes))
        page2angle = {1: 90., 2: 90., 3: 270., 4: 270., 5: 180., 6: 270., 7: 180., 8: 270.}

        for result_node in result.nodes:
            wrapped_node = PageNodeWrapper.wrap(result_node)
            self.assertIsNotNone(wrapped_node.angle, f"Page {wrapped_node.metadata.number}")
            self.assertEqual(page2angle[wrapped_node.metadata.number], wrapped_node.angle, f"Page {wrapped_node.metadata.number}")
