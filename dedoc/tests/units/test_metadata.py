import os
import unittest

from dedoc.metadata_extractor.concreat_metadata_extractors.docx_metadata_extractor import DocxMetadataExtractor


class TestMetadataExtractor(unittest.TestCase):
    extractor = DocxMetadataExtractor()

    def test_docx_metadata_broken_file(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "docx", "broken.docx")
        path = os.path.abspath(path)
        self.assertDictEqual({"broken_docx": True}, self.extractor._get_docx_fields(path))
