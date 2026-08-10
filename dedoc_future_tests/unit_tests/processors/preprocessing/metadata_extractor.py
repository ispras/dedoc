from pathlib import Path
from unittest import TestCase

from tdm import TalismanDocumentFactory

from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.processors.preprocessing.metadata_extractor import MetadataExtractor


class TestMetadataExtractor(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.resolve() / "tests" / "data"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = MetadataExtractor()

    def test_pdf(self) -> None:
        file_path = self.data_path / "pdf_with_text_layer" / "example.pdf"
        result = self.processor.process(self.document, [FileNode(str(file_path))], ImmutableBaseModel())

        self.assertEqual(1, len(result.nodes))
        self.assertEqual(0, len(result.structure))

        file_node = result.nodes[0]
        self.assertEqual("example.pdf", file_node.metadata.name)
        self.assertEqual(187058, file_node.metadata.size)
        self.assertEqual("application/pdf", file_node.metadata.mime)
        self.assertEqual(".pdf", file_node.metadata.extension)
        self.assertLess(1660000000, file_node.metadata.modified_time)
        self.assertLess(1660000000, file_node.metadata.created_time)
        self.assertLess(file_node.metadata.created_time, file_node.metadata.access_time)

    def test_image(self) -> None:
        file_path = self.data_path / "scanned" / "example.jpg"
        result = self.processor.process(self.document, [FileNode(str(file_path))], ImmutableBaseModel())

        self.assertEqual(1, len(result.nodes))
        self.assertEqual(0, len(result.structure))

        file_node = result.nodes[0]
        self.assertEqual("example.jpg", file_node.metadata.name)
        self.assertEqual(36009, file_node.metadata.size)
        self.assertEqual("image/jpeg", file_node.metadata.mime)
        self.assertEqual(".jpg", file_node.metadata.extension)
        self.assertLess(1660000000, file_node.metadata.modified_time)
        self.assertLess(1660000000, file_node.metadata.created_time)
        self.assertLess(file_node.metadata.created_time, file_node.metadata.access_time)
