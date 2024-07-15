import os
import unittest

from dedoc.dedoc_manager import DedocManager
from dedoc.utils.langchain import make_manager_config, make_manager_pdf_config


class TestLangchainDocumentLoader(unittest.TestCase):
    test_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "data")
    test_files = [
        "archives/zipka.zip", "archives/zipka.tar", "archives/zipka.rar", "archives/zipka.7z",
        "csvs/csv_coma.csv", "csvs/csv_tab.tsv",
        "docx/english_doc.docx", "docx/english_doc.doc", "docx/english_doc.odt", "docx/english_doc.rtf",
        "xlsx/example.xlsx", "xlsx/example.xls", "xlsx/example.ods",
        "pptx/example.pptx", "pptx/example.ppt", "pptx/example.odp",
        "htmls/example.html", "eml/message.eml", "mhtml/with_attachments.mhtml",
        "json/example2.json", "txt/example.txt", "xml/simple.xml",
        "scanned/example.png", "scanned/example.pdf", "scanned/example.jpg", "scanned/example_with_table7.djvu",
        "pdf_auto/mixed_pdf.pdf", "pdf_with_text_layer/example.pdf",
    ]

    def test_make_manager_config(self) -> None:
        for file in self.test_files:
            manager_config = make_manager_config(file_path=os.path.join(self.test_folder_path, file), split="node", parsing_params={})
            manager = DedocManager(manager_config=manager_config)
            manager.parse(file_path=os.path.join(self.test_folder_path, file))

    def test_make_manager_pdf_config(self) -> None:
        pdf_file_path = os.path.join(self.test_folder_path, "pdf_auto", "mixed_pdf.pdf")
        for pdf_with_text_layer in ("true", "tabby", "false", "auto", "auto_tabby"):
            manager_config = make_manager_pdf_config(file_path=pdf_file_path, split="node", parsing_params=dict(pdf_with_text_layer=pdf_with_text_layer))
            manager = DedocManager(manager_config=manager_config)
            manager.parse(file_path=pdf_file_path, parameters=dict(pdf_with_text_layer=pdf_with_text_layer))

    def test_dedoc_file_loader(self) -> None:
        from dedoc_loader import DedocFileLoader

        for file in self.test_files:
            loader = DedocFileLoader(os.path.join(self.test_folder_path, file), split="document", with_tables=False)
            docs = loader.load()
            self.assertEqual(1, len(docs))

    def test_dedoc_api_loader(self) -> None:
        from dedoc_loader import DedocAPIFileLoader

        dedoc_url = f"http://{os.environ.get('DOC_READER_HOST', '0.0.0.0')}:1231"
        for file in self.test_files:
            loader = DedocAPIFileLoader(os.path.join(self.test_folder_path, file), url=dedoc_url, split="document", with_tables=False)
            docs = loader.load()
            self.assertEqual(1, len(docs))

    def test_dedoc_pdf_loader(self) -> None:
        from pdf import DedocPDFLoader

        pdf_file_path = os.path.join(self.test_folder_path, "pdf_auto", "mixed_pdf.pdf")
        for mode in ("true", "tabby", "false", "auto", "auto_tabby"):
            loader = DedocPDFLoader(pdf_file_path, split="document", with_tables=False, pdf_with_text_layer=mode)
            docs = loader.load()
            self.assertEqual(1, len(docs))

    def test_dedoc_base_loader(self) -> None:
        from dedoc_loader import DedocFileLoader

        file_path = os.path.join(self.test_folder_path, "with_attachments", "example_with_attachments_depth_1.pdf")

        for split in ("line", "page", "node"):
            loader = DedocFileLoader(file_path, split=split, with_tables=False)
            docs = loader.load()
            if split == "page":
                self.assertEqual(1, len(docs))
            else:
                self.assertGreater(len(docs), 1)

        loader = DedocFileLoader(
            file_path, split="document", with_tables=True, with_attachments=True, need_content_analysis=True, need_pdf_table_analysis=False
        )
        text_docs, table_docs, attachment_docs = [], [], []
        for doc in loader.load():
            doc_type = doc.metadata.get("type", "")
            if doc_type == "table":
                table_docs.append(doc)
                self.assertIn("text_as_html", doc.metadata)
            elif doc_type == "attachment":
                attachment_docs.append(doc)
            else:
                text_docs.append(doc)

        self.assertEqual(1, len(text_docs))
        self.assertEqual(1, len(table_docs))
        self.assertEqual(5, len(attachment_docs))
