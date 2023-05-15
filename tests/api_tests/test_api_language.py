import os.path

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "docx")

    def test_en_doc(self) -> None:
        file_name = "english_doc.doc"
        result = self._send_request(file_name, dict(language="eng", structure_type="tree"))
        self.check_english_doc(result)

    def test_en_docx(self) -> None:
        file_name = "english_doc.docx"
        result = self._send_request(file_name, dict(language="eng", structure_type="tree"))
        self.check_english_doc(result)

    def test_en_odt(self) -> None:
        file_name = "english_doc.odt"
        result = self._send_request(file_name, dict(language="eng", structure_type="tree"))
        self.check_english_doc(result)

    def test_en_pdf(self) -> None:
        file_name = "../pdf_with_text_layer/english_doc.pdf"
        result = self._send_request(file_name, dict(language="eng"))
        self.check_english_doc(result)
