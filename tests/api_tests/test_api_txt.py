from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiTxtReader(AbstractTestApiDocReader):

    def test_txt_file(self):
        file_name = "Pr_2013.02.18_21.txt"
        result = self._send_request(file_name)

    def test_text(self):
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    def test_text2(self):
        file_name = "pr_17.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        res = str(content)
        self.assertFalse("ufeff" in res)
