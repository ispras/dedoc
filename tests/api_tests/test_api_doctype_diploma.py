import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDiploma(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "diplomas", file_name)

    def test_diploma_pdf(self) -> None:
        file_name = "diploma.pdf"
        result = self._send_request(file_name, dict(document_type="diploma", pdf_with_text_layer="tabby"))
        structure = result["content"]["structure"]

        node = self._get_by_tree_path(structure, "0")
        self.assertEqual("Москва, 2021 г.", node["text"].strip()[-15:])
        self.assertEqual("root", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.0")
        self.assertEqual("", node["text"])
        self.assertEqual("body", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.1")
        self.assertEqual("СОДЕРЖАНИЕ", node["text"].strip())
        self.assertEqual("toc", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.1.0")
        self.assertEqual("ВВЕДЕНИЕ", node["text"][:8])
        self.assertEqual("toc_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.2")
        self.assertEqual("ВВЕДЕНИЕ", node["text"].strip())
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.3")
        self.assertEqual("1. ТЕОРЕТИЧЕСКОЕ", node["text"][:16])
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.4")
        self.assertEqual("2. АНАЛИЗ", node["text"][:9])
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.5")
        self.assertEqual("ЗАКЛЮЧЕНИЕ", node["text"].strip())
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.6")
        self.assertEqual("БИБЛИОГРАФИЧЕСКИЙ СПИСОК", node["text"].strip())
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

    def test_diploma_docx(self) -> None:
        file_name = "diploma.docx"
        result = self._send_request(file_name, dict(document_type="diploma"))
        structure = result["content"]["structure"]

        node = self._get_by_tree_path(structure, "0")
        self.assertEqual("Москва 2023 г.", node["text"].strip()[-14:])
        self.assertEqual("root", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.0")
        self.assertEqual("", node["text"])
        self.assertEqual("body", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.1")
        self.assertEqual("Содержание", node["text"].strip())
        self.assertEqual("toc", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.1.0")
        self.assertEqual("Введение", node["text"][:8])
        self.assertEqual("toc_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.2")
        self.assertEqual("Введение", node["text"].strip())
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.3")
        self.assertEqual("Глава 1.", node["text"][:8])
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.4")
        self.assertEqual("Глава 2.", node["text"][:8])
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.5")
        self.assertEqual("Глава 3.", node["text"][:8])
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(structure, "0.6")
        self.assertEqual("Список литературы", node["text"].strip())
        self.assertEqual("named_item", node["metadata"]["paragraph_type"])
