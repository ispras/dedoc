from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiAttachmentsReader(AbstractTestApiDocReader):

    def test_wo_attachments_excel(self):
        file_name = "example.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        self.assertEqual([], result['attachments'])

    def test_get_attachments_xlxs_depth_1(self):
        file_name = "example_with_images.xlsx"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result['attachments']

    def test_get_attachments_xls_depth_1(self):
        file_name = "example_with_images.xls"
        result = self._send_request(file_name, dict(with_attachments=True))
        attachments = result['attachments']

