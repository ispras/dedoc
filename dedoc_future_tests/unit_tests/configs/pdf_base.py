from unittest import TestCase

from dedoc_future.configs.pdf_base import PdfBaseConfig


class TestPdfBaseConfig(TestCase):
    def test_incorrect_page_range(self) -> None:
        with self.assertRaises(ValueError):
            _ = PdfBaseConfig(end_page=0)

        with self.assertRaises(ValueError):
            _ = PdfBaseConfig(end_page=-1)

        with self.assertRaises(ValueError):
            _ = PdfBaseConfig(start_page=1, end_page=0)

        with self.assertRaises(ValueError):
            _ = PdfBaseConfig(start_page=2, end_page=1)

    def test_correct_page_range(self) -> None:
        config = PdfBaseConfig()
        self.assertEqual(0, config.start_page)

        config = PdfBaseConfig(start_page=1, end_page=1)
        self.assertEqual(0, config.start_page)
        self.assertEqual(1, config.end_page)

        config = PdfBaseConfig(start_page=2, end_page=10)
        self.assertEqual(1, config.start_page)
        self.assertEqual(10, config.end_page)
