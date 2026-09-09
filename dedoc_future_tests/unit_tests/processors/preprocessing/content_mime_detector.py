import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

from tdm import TalismanDocumentFactory

from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.datamodel.nodes.file import FileNode
from dedoc_future.processors.preprocessing.content_mime_detector import ContentMimeDetector


class TestContentMimeDetector(TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).parent.parent.parent.parent.parent.resolve() / "tests" / "data"
        self.document = TalismanDocumentFactory().create_document()
        self.processor = ContentMimeDetector()
        self.file_names = [
            "archives/arch_with_attachs.7z", "archives/arch_with_attachs.rar", "archives/arch_with_attachs.tar", "archives/arch_with_attachs.tar.gz",
            "archives/arch_with_attachs.zip", "csvs/csv_coma.csv", "docx/english_doc.doc", "docx/english_doc.docx",
            "docx/english_doc.odt", "docx/english_doc.rtf", "pdf_with_text_layer/english_doc.pdf", "scanned/example.bmp",
            "scanned/example.eps", "scanned/example.gif", "scanned/example.jpg", "scanned/example.pcx", "scanned/example.pdf", "scanned/example.png",
            "scanned/example.ppm", "scanned/example.ras", "scanned/example.tiff", "scanned/example.webp", "htmls/example.html",
            "xlsx/example.ods", "xlsx/example.xls", "xlsx/example.xlsx", "pptx/example.ppt", "pptx/example.pptx", "json/dict.json",
            "scanned/example_with_table9.djvu", "txt/football.txt", "xml/simple.xml"
        ]

    def test_correct(self) -> None:
        file_path = self.data_path / "pdf_with_text_layer" / "example.pdf"
        result = self.processor.process(self.document, [FileNode(str(file_path))], ImmutableBaseModel())

        self.assertEqual(1, len(result.nodes))
        self.assertEqual(0, len(result.structure))

        file_node = result.nodes[0]
        self.assertEqual("application/pdf", file_node.metadata.mime)
        self.assertEqual(".pdf", file_node.metadata.extension)

    def test_incorrect_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            for file_name in self.file_names:
                extension = "docx" if file_name.endswith("png") else "png"
                file_path = self.data_path / file_name
                tmp_file_path = Path(tmp_dir) / f"file.{extension}"
                shutil.copyfile(file_path, tmp_file_path)
                result = self.processor.process(self.document, [FileNode(str(tmp_file_path))], ImmutableBaseModel())
                file_node = result.nodes[0]
                self.assertEqual(file_path.suffix, file_node.metadata.extension, file_name)

    def test_without_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            for file_name in self.file_names:
                file_path = self.data_path / file_name
                tmp_file_path = Path(tmp_dir) / "file"
                shutil.copyfile(file_path, tmp_file_path)
                result = self.processor.process(self.document, [FileNode(str(tmp_file_path))], ImmutableBaseModel())
                file_node = result.nodes[0]
                self.assertEqual(file_path.suffix, file_node.metadata.extension, file_name)

    def test_unknown(self) -> None:
        file_path = self.data_path / "file.bin"
        result = self.processor.process(self.document, [FileNode(str(file_path))], ImmutableBaseModel())
        file_node = result.nodes[0]
        self.assertEqual("application/octet-stream", file_node.metadata.mime)
        self.assertEqual(".bin", file_node.metadata.extension)
