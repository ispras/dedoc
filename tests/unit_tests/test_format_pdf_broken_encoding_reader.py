import os
import unittest

import Levenshtein

from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding_reader import PdfBrokenEncodingReader


class TestPdfBrokenEncodingReader(unittest.TestCase):
    def test_pdf_broken_encoding(self) -> None:
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "data", "pdf_with_text_layer", "mongolo.pdf")
        orig_path = os.path.join(os.path.dirname(__file__), "..", "data", "txt", "mongolo.txt")
        reader = PdfBrokenEncodingReader()
        result = reader.read(file_path=pdf_path)
        lines = "".join([i.line for i in result.lines[0:10]])
        with open(orig_path, encoding="utf8", mode="r") as txt:
            accuracy = Levenshtein.ratio(txt.read(), lines)
            self.assertTrue(accuracy > 0.7)
