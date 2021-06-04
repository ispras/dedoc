from tests.abstrac_api_test import AbstractTestApiDocReader
from tests.test_utils import get_by_tree_path


class TestApiDocReader(AbstractTestApiDocReader):

    def test_tricky_doc(self):
        file_name = "doc.docx"
        result = self._send_request(file_name)

    def test_text(self):
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data=dict(structure_type="tree"))
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    def test_bin_file(self):
        self._send_request("file.bin", expected_code=415)
