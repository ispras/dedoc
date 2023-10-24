import os

from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from tests.test_utils import get_test_config


class TestLawTxtReader(AbstractTestApiDocReader):
    config = get_test_config()
    txt_reader = RawTextReader(config=config)
    metadata_extractor = BaseMetadataExtractor()
    law_extractor = LawStructureExtractor(config=config)

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "laws", file_name)

    def test_law_document_spaces_correctness(self) -> None:
        path = self._get_abs_path("коап_москвы_8_7_2015_utf.txt")
        directory, filename = os.path.split(path)
        document = self.txt_reader.read(path=path, document_type="law", parameters={})
        document.metadata = self.metadata_extractor.extract_metadata(directory, filename, filename, filename)
        document = self.law_extractor.extract_structure(document, {})

        self.assertListEqual([], document.attachments)
        self.assertListEqual([], document.tables)
        lines = document.lines
        self.assertEqual("\n", lines[0].line)
        self.assertEqual(0, lines[0].metadata.line_id)
        self.assertEqual("    \n", lines[1].line)
        self.assertEqual(1, lines[1].metadata.line_id)
        self.assertEqual("\n", lines[2].line)
        self.assertEqual(2, lines[2].metadata.line_id)
        self.assertEqual("   \n", lines[3].line)
        self.assertEqual(3, lines[3].metadata.line_id)
        self.assertEqual("ЗАКОН\n", lines[4].line)
        self.assertEqual(4, lines[4].metadata.line_id)
