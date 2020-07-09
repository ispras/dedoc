from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiTxtReader(AbstractTestApiDocReader):

    def test_txt_file(self):
        file_name = "Pr_2013.02.18_21.txt"
        result = self._send_request(file_name)
