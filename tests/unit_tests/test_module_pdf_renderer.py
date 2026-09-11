import os
import unittest

import numpy as np

from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from tests.test_utils import get_test_config


class TestPdfRenderer(unittest.TestCase):
    """
    The image based readers rasterize PDF pages with poppler (pdf2image) by default and with pypdfium2 when
    config["pdf_renderer"] is set to "pdfium". Both must produce the same pages at the same resolution.
    """

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "scanned")), file_name)

    def _render(self, renderer: str, file_name: str) -> list:
        config = dict(get_test_config())
        config["pdf_renderer"] = renderer
        reader = PdfImageReader(config=config)
        return list(reader._split_pdf2image(self._get_abs_path(file_name), 0, 10))

    def test_pdftoppm_is_the_default(self) -> None:
        self.assertEqual("pdftoppm", get_test_config().get("pdf_renderer", "pdftoppm"))

    def test_renderers_produce_the_same_pages(self) -> None:
        for file_name in ("example.pdf", "doc_with_long_list.pdf"):
            with self.subTest(file_name=file_name):
                poppler_pages = self._render("pdftoppm", file_name)
                pdfium_pages = self._render("pdfium", file_name)

                self.assertEqual(len(poppler_pages), len(pdfium_pages))
                self.assertGreater(len(pdfium_pages), 0)
                for poppler_page, pdfium_page in zip(poppler_pages, pdfium_pages):
                    # same resolution (200 DPI) and colour convention, so the stages after rendering do not care
                    self.assertEqual(poppler_page.shape, pdfium_page.shape)
                    # the two rasterizers anti-alias differently, but the page has to be the same page
                    difference = np.abs(poppler_page.astype(np.int16) - pdfium_page.astype(np.int16)).mean()
                    self.assertLess(difference, 20)

    def test_unknown_renderer_falls_back_to_poppler(self) -> None:
        expected = self._render("pdftoppm", "example.pdf")
        actual = self._render("something-else", "example.pdf")

        self.assertEqual(len(expected), len(actual))
        for expected_page, actual_page in zip(expected, actual):
            self.assertTrue(np.array_equal(expected_page, actual_page))
