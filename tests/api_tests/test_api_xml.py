import os

from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiXML(AbstractTestApiDocReader):

    data_directory_path = os.path.join(AbstractTestApiDocReader.data_directory_path, "xml")

    def test_xml(self) -> None:
        file_name = "simple.xml"
        result = self._send_request(file_name)
        subparagraphs = result["content"]["structure"]["subparagraphs"]
        self.assertEqual('<?xml version="1.0" encoding="utf-8"?>\n', subparagraphs[0]["text"])
        self.assertEqual('<note>\n', subparagraphs[1]["text"])
        self.assertEqual(' <to>\n', subparagraphs[2]["text"])
        self.assertEqual('  Tove\n', subparagraphs[3]["text"])
        self.assertEqual(' </to>\n', subparagraphs[4]["text"])
        self.assertEqual('</note>', subparagraphs[5]["text"])
