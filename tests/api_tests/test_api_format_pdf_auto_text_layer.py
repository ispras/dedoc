import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfAutoTextLayer(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_auto", file_name)

    def test_pdf_auto_auto_columns(self) -> None:
        file_name = "0004057v1.pdf"
        parameters = dict(with_attachments=True, pdf_with_text_layer="auto", is_one_column_document="auto")
        result = self._send_request(file_name, parameters)
        warnings = result["warnings"]
        self.assertIn("Assume document has a correct textual layer", warnings)

    def test_pdf_auto_auto_columns_each_page_have_different_columns(self) -> None:
        file_name = "liao2020_merged_organized.pdf"
        parameters = dict(with_attachments=True, pdf_with_text_layer="auto", is_one_column_document="auto")
        result = self._send_request(file_name, parameters)
        warnings = result["warnings"]
        self.assertIn("Assume document has a correct textual layer", warnings)

    def test_pdf_auto_auto_columns_each_page_have_same_columns_except_first(self) -> None:
        file_name = "liao2020_merged-1-5.pdf"
        parameters = dict(with_attachments=True, pdf_with_text_layer="auto", is_one_column_document="auto")
        result = self._send_request(file_name, parameters)
        warnings = result["warnings"]
        self.assertIn("Assume document has a correct textual layer", warnings)

    def test_pdf_auto_text_layer_2(self) -> None:
        file_name = "e09d__cs-pspc-xg-15p-portable-radio-quick-guide.pdf"
        self._send_request(file_name, dict(with_attachments=True, pdf_with_text_layer="auto"))

    def test_auto_pdf_with_scans(self) -> None:
        file_name = "tz_scan_1page.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="auto"))
        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)
        self.assertIn("Техническое задание", self._get_by_tree_path(tree, "0.0")["text"])

    def test_auto_pdf_with_text_layer(self) -> None:
        file_name = os.path.join("..", "pdf_with_text_layer", "english_doc.pdf")
        result = self._send_request(file_name, dict(pdf_with_text_layer="auto"))
        self.assertIn("Assume document has a correct textual layer", result["warnings"])
        self._check_english_doc(result)

    def test_auto_pdf_with_wrong_text_layer(self) -> None:
        file_name = "english_doc_bad_text.pdf"
        result = self._send_request(file_name, dict(pdf_with_text_layer="auto"))
        self.assertIn("Assume document has incorrect textual layer", result["warnings"])
        self._check_english_doc(result)

    def test_auto_document_mixed(self) -> None:
        file_name = "mixed_pdf.pdf"
        for pdf_with_text_layer in "auto", "auto_tabby":
            result = self._send_request(file_name, dict(pdf_with_text_layer=pdf_with_text_layer))
            self.assertIn("Assume document has a correct textual layer", result["warnings"])
            self.assertIn("Assume the first page hasn"t a textual layer", result["warnings"])
            self._check_english_doc(result)
            structure = result["content"]["structure"]
            list_items = structure["subparagraphs"][1]["subparagraphs"]
            self.assertEqual("3) продолжаем список\n", list_items[2]["text"])
            self.assertEqual("4) Список идёт своим чередом\n", list_items[3]["text"])
            self.assertEqual("5) заканчиваем список\n", list_items[4]["text"])
            self.assertEqual("6) последний элемент списка.\n", list_items[5]["text"])

    def test_auto_partially_read(self) -> None:
        file_name = "mixed_pdf.pdf"
        data = {"pdf_with_text_layer": "auto", "pages": "2:"}
        result = self._send_request(file_name, data)
        structure = result["content"]["structure"]
        self.assertEqual("", structure["subparagraphs"][0]["text"])
        list_items = structure["subparagraphs"][1]["subparagraphs"]
        self.assertEqual("3) продолжаем список\n", list_items[0]["text"])
        self.assertEqual("4) Список идёт своим чередом\n", list_items[1]["text"])
        self.assertEqual("5) заканчиваем список\n", list_items[2]["text"])
        self.assertEqual("6) последний элемент списка.\n", list_items[3]["text"])
    
    def test_fast_textual_layer_detection(self) -> None:
        file_name = "0004057v1.pdf"
        parameters = dict(pdf_with_text_layer="auto", fast_textual_layer_detection=True)
        result = self._send_request(file_name, parameters)
        warnings = result["warnings"]
        self.assertIn("Assume document has a correct textual layer", warnings)
        self.assertEqual(result["content"]["structure"]["subparagraphs"][5]["text"][:10], "This paper")

        parameters = dict(pdf_with_text_layer="auto_tabby", fast_textual_layer_detection=True)
        result = self._send_request(file_name, parameters)
        warnings = result["warnings"]
        self.assertIn("Assume document has a correct textual layer", warnings)
        self.assertEqual(result["content"]["structure"]["subparagraphs"][5]["text"][:10], "This paper")
