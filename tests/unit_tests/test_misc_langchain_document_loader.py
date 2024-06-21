import os
import unittest

from dedoc.utils.langchain import make_manager_config, make_manager_pdf_config


class TestLangchainDocumentLoader(unittest.TestCase):
    test_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "data")
    test_files = [
        "/docx/example.docx",
        "/pptx/example.pptx",
        "laws/doc_000008.html",
        "/eml/message.eml",
        "/mhtml/with_attachments.mhtml",
        "/archives/zipka.rar",
        "/scanned/example.jpg",
        "/pdf_auto/mixed_pdf.pdf",
        "/txt/example.txt",
        "/json/example2.json"
    ]

    def test_basic_parts(self) -> None:
        for file in self.test_files:
            config = make_manager_config(file_path=os.path.join(self.test_folder_path, file), split="line", parsing_params={})
            self.assertEqual(len(config["reader"].readers), 1)
            self.assertEqual(len(config["document_metadata_extractor"].extractors), 1)
            self.assertIn("linear", config["structure_constructor"].constructors.keys())

    def test_converter(self) -> None:
        config = make_manager_config(file_path=os.path.join(self.test_folder_path, "/docx/example.docx"), split="line", parsing_params={})
        self.assertEqual(len(config["converter"].converters), 1)

    def test_manager_pdf_config(self) -> None:
        config = make_manager_pdf_config(file_path=os.path.join(self.test_folder_path, "/pdf_auto/mixed_pdf.pdf"), split="line", parsing_params={})
        self.assertEqual(len(config["reader"].readers), 1)
        self.assertEqual(len(config["converter"].converters), 1)
        self.assertEqual(len(config["document_metadata_extractor"].extractors), 1)
        self.assertIn("linear", config["structure_constructor"].constructors.keys())
