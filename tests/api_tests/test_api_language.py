import os.path

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "docx")

    def test_en_doc(self) -> None:
        file_name = "english_doc.doc"
        result = self._send_request(file_name, dict(language="eng", structure_type="tree"))
        content = result["content"]
        structure = content["structure"]

        self.assertEqual("THE GREAT ENGLISH DOCUMENT", structure["subparagraphs"][0]["text"])
        list_elements = structure["subparagraphs"][1]["subparagraphs"]
        self.assertEqual("1) Fisrst item", list_elements[0]["text"])
        self.assertEqual("2) Second item", list_elements[1]["text"])

        table = content["tables"][0]
        self.assertListEqual(['London', 'The capital of Great Britain'], table["cells"][0])
        self.assertListEqual(['Speek', 'From my heart'], table["cells"][1])

    def test_en_docx(self) -> None:
        file_name = "english_doc.docx"
        result = self._send_request(file_name, dict(language="eng", structure_type="tree"))
        content = result["content"]
        structure = content["structure"]

        self.assertEqual("THE GREAT ENGLISH DOCUMENT", structure["subparagraphs"][0]["text"])
        list_elements = structure["subparagraphs"][1]["subparagraphs"]
        self.assertEqual("1) Fisrst item", list_elements[0]["text"])
        self.assertEqual("2) Second item", list_elements[1]["text"])

        table = content["tables"][0]
        self.assertListEqual(['London', 'The capital of Great Britain'], table["cells"][0])
        self.assertListEqual(['Speek', 'From my heart'], table["cells"][1])

    def test_en_odt(self) -> None:
        file_name = "english_doc.odt"
        result = self._send_request(file_name, dict(language="eng", structure_type="tree"))
        content = result["content"]
        structure = content["structure"]

        self.assertEqual("THE GREAT ENGLISH DOCUMENT", structure["subparagraphs"][0]["text"])
        list_elements = structure["subparagraphs"][1]["subparagraphs"]
        self.assertEqual("1) Fisrst item", list_elements[0]["text"])
        self.assertEqual("2) Second item", list_elements[1]["text"])

        table = content["tables"][0]
        self.assertListEqual(['London', 'The capital of Great Britain'], table["cells"][0])
        self.assertListEqual(['Speek', 'From my heart'], table["cells"][1])
