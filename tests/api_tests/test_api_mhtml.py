from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiMhtmlReader(AbstractTestApiDocReader):
    def test_mhtml(self) -> None:
        file_name = "mhtml/Валентин Николаевич Ничипоренко биография, досье, компромат, фото и видео - ЗНАЙ ЮА.mhtml"
        result = self._send_request(file_name, dict(with_attachments=True), expected_code=200)
        self.assertEqual(17, len(result["attachments"]))
