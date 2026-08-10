from pathlib import Path
from unittest import TestCase

from tdm import TalismanDocumentFactory

from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.metadata.file import FileMetadata
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.processors.parsing.pdf.render.pages_creator import PagesCreator


class TestPagesCreator(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent.resolve() / "tests" / "data"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = PagesCreator()

    def test_pdf(self) -> None:
        file_path = self.data_path / "pdf_with_text_layer" / "example.pdf"
        node = FileNode(str(file_path), metadata=FileMetadata(extension=".pdf", need_parse=True))
        result = self.processor.process(self.document, [node], PdfBaseConfig())

        self.assertEqual(1, len(result.nodes))
        self.assertEqual(node, result.nodes[0])
        self.assertEqual(1, len(result.structure))

        page_nodes = list(result.structure[node])
        self.assertEqual(1, len(page_nodes))
        self.assertTrue(isinstance(page_nodes[0], PageNode))
        self.assertEqual(node, page_nodes[0].metadata.file_ref)
        self.assertEqual(0, page_nodes[0].metadata.number)

    def test_page_range(self) -> None:
        file_path = self.data_path / "pdf_with_text_layer" / "multipage.pdf"
        node = FileNode(str(file_path), metadata=FileMetadata(extension=".pdf", need_parse=True))

        for start_page, end_page in [(1, 1), (1, 2), (2, 2), (2, 3), (5, 8), (9, 9)]:
            config = PdfBaseConfig(start_page=start_page, end_page=end_page)
            result = self.processor.process(self.document, [node], config)
            self.assertEqual(1, len(result.structure))
            page_nodes = list(result.structure[node])
            self.assertEqual(end_page - start_page + 1, len(page_nodes))
            self.assertListEqual(list(range(start_page - 1, end_page)), [page.metadata.number for page in page_nodes])

        for start_page in (1, 2, 9):
            config = PdfBaseConfig(start_page=start_page)
            result = self.processor.process(self.document, [node], config)
            self.assertEqual(1, len(result.structure))
            page_nodes = list(result.structure[node])
            self.assertEqual(10 - start_page, len(page_nodes))
            self.assertListEqual(list(range(start_page - 1, 9)), [page.metadata.number for page in page_nodes])

    def test_page_out_of_limit(self) -> None:
        file_path = self.data_path / "pdf_with_text_layer" / "multipage.pdf"
        node = FileNode(str(file_path), metadata=FileMetadata(extension=".pdf", need_parse=True))

        for start_page, end_page in [(10, 11), (11, None)]:
            config = PdfBaseConfig(start_page=start_page, end_page=end_page)
            result = self.processor.process(self.document, [node], config)
            self.assertEqual(0, len(result.structure))

        result = self.processor.process(self.document, [node], PdfBaseConfig(end_page=11))
        self.assertEqual(1, len(result.structure))
        page_nodes = list(result.structure[node])
        self.assertEqual(9, len(page_nodes))
        self.assertListEqual(list(range(9)), [page.metadata.number for page in page_nodes])

    def test_image(self) -> None:
        file_path = self.data_path / "scanned" / "example.jpg"
        node = FileNode(str(file_path), metadata=FileMetadata(extension=".jpg", need_parse=True))
        result = self.processor.process(self.document, [node], PdfBaseConfig())

        self.assertEqual(1, len(result.nodes))
        self.assertEqual(node, result.nodes[0])
        self.assertEqual(1, len(result.structure))

        page_nodes = list(result.structure[node])
        self.assertEqual(1, len(page_nodes))

        page_node = PageNodeWrapper.wrap(page_nodes[0])
        self.assertEqual(node, page_node.metadata.file_ref)
        self.assertEqual(0, page_node.metadata.number)
        self.assertIsNotNone(page_node.image)
