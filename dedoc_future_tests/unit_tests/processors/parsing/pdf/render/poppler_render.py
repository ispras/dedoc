from pathlib import Path
from unittest import TestCase

from tdm import TalismanDocumentFactory

from dedoc_future.configs.pdf_base import PdfBaseConfig
from dedoc_future.datamodel.metadata.page import PageMetadata
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.datamodel.nodes.page import PageNode, PageNodeWrapper
from dedoc_future.processors.parsing.pdf.render.poppler_render import PopplerRender


class TestPopplerRender(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent.resolve() / "tests" / "data"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = PopplerRender()

    def test_multipage(self) -> None:
        file_path = self.data_path / "pdf_with_text_layer" / "multipage.pdf"
        file_node = FileNode(str(file_path))
        page_nodes = [PageNode(metadata=PageMetadata(file_ref=file_node, number=i)) for i in range(5)]
        result = self.processor.process(self.document, page_nodes, PdfBaseConfig())

        self.assertEqual(len(page_nodes), len(result.nodes))
        for node in result.nodes:
            node = PageNodeWrapper.wrap(node)
            self.assertIsNotNone(node.image)
            self.assertIsNotNone(node.orig_image)
            self.assertEqual((2339, 1654, 3), node.orig_image.shape)
