import os
import re
import unittest

from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import DefaultStructureExtractor
from dedoc.structure_extractors.patterns.dotted_list_pattern import DottedListPattern
from dedoc.structure_extractors.patterns.regexp_pattern import RegexpPattern
from dedoc.structure_extractors.patterns.roman_list_pattern import RomanListPattern
from dedoc.structure_extractors.patterns.tag_header_pattern import TagHeaderPattern
from dedoc.structure_extractors.patterns.tag_list_pattern import TagListPattern
from tests.test_utils import get_test_config


class TestDefaultStructureExtractor(unittest.TestCase):
    data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    structure_extractor = DefaultStructureExtractor(config=get_test_config())
    reader = ReaderComposition(readers=[RawTextReader(), DocxReader()])

    def test_tag_patterns(self) -> None:
        file_path = os.path.join(self.data_directory_path, "docx", "with_tags.docx")
        patterns = [
            TagHeaderPattern(line_type="custom_header", level_1=1, can_be_multiline=False),
            TagListPattern(line_type="custom_list", level_1=2),
        ]
        document = self.reader.read(file_path=file_path)
        document = self.structure_extractor.extract(document=document, parameters={"patterns": patterns})
        self.assertEqual(document.lines[0].metadata.hierarchy_level.line_type, "custom_header")
        self.assertEqual(document.lines[0].metadata.hierarchy_level.level_1, 1)
        self.assertEqual(document.lines[0].metadata.hierarchy_level.level_2, 1)
        self.assertFalse(document.lines[0].metadata.hierarchy_level.can_be_multiline)

        self.assertEqual(document.lines[1].metadata.hierarchy_level.line_type, "custom_header")
        self.assertEqual(document.lines[1].metadata.hierarchy_level.level_1, 1)
        self.assertEqual(document.lines[1].metadata.hierarchy_level.level_2, 2)

        self.assertEqual(document.lines[3].metadata.hierarchy_level.line_type, "raw_text")
        self.assertTrue(document.lines[3].metadata.hierarchy_level.can_be_multiline)

        self.assertEqual(document.lines[4].metadata.hierarchy_level.line_type, "custom_list")
        self.assertEqual(document.lines[4].metadata.hierarchy_level.level_1, 2)
        self.assertEqual(document.lines[4].metadata.hierarchy_level.level_2, 1)
        self.assertFalse(document.lines[4].metadata.hierarchy_level.can_be_multiline)

    def test_list_patterns(self) -> None:
        file_path = os.path.join(self.data_directory_path, "txt", "pr_17.txt")
        patterns = [
            RomanListPattern(line_type="chapter", level_1=1, level_2=1, can_be_multiline=False),
            DottedListPattern(line_type="dotted_list", level_1=2, can_be_multiline=False),
        ]
        document = self.reader.read(file_path=file_path)
        document = self.structure_extractor.extract(document=document, parameters={"patterns": patterns})

        self.assertEqual(document.lines[0].metadata.hierarchy_level.line_type, "raw_text")
        self.assertEqual(document.lines[12].metadata.hierarchy_level.line_type, "chapter")
        self.assertEqual(document.lines[14].metadata.hierarchy_level.line_type, "dotted_list")

    def test_regexp_patterns(self) -> None:
        file_path = os.path.join(self.data_directory_path, "docx", "without_numbering.docx")
        patterns = [
            RegexpPattern(regexp="^глава\s\d+\.", line_type="глава", level_1=1),  # noqa
            RegexpPattern(regexp=re.compile(r"^статья\s\d+\.\d+\."), line_type="статья", level_1=2)
        ]
        document = self.reader.read(file_path=file_path)
        document = self.structure_extractor.extract(document=document, parameters={"patterns": patterns})
        self.assertEqual(document.lines[0].metadata.hierarchy_level.line_type, "raw_text")
        self.assertEqual(document.lines[9].metadata.hierarchy_level.line_type, "глава")
        self.assertEqual(document.lines[11].metadata.hierarchy_level.line_type, "статья")
        self.assertEqual(document.lines[15].metadata.hierarchy_level.line_type, "статья")
        self.assertEqual(document.lines[83].metadata.hierarchy_level.line_type, "глава")

    def test_start_word_patterns(self) -> None:
        file_path = os.path.join(self.data_directory_path, "docx", "example.docx")
        patterns = [
            {"name": "start_word", "start_word": "глава", "level_1": 1, "line_type": "глава"},
            {"name": "start_word", "start_word": "статья", "level_1": 2, "line_type": "статья"},
        ]
        document = self.reader.read(file_path=file_path)
        document = self.structure_extractor.extract(document=document, parameters={"patterns": patterns})
        self.assertEqual(document.lines[1].metadata.hierarchy_level.line_type, "глава")
        self.assertEqual(document.lines[3].metadata.hierarchy_level.line_type, "статья")
        self.assertEqual(document.lines[5].metadata.hierarchy_level.line_type, "статья")
