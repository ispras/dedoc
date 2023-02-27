import unittest

from dedoc.readers.utils.hierarchy_level_extractor import HierarchyLevelExtractor


class TestUtilsRegexps(unittest.TestCase):
    extractor = HierarchyLevelExtractor()

    def test_chapter_regexp(self) -> None:
        self.assertTrue(self.extractor.chapter.fullmatch('статья 1.'))
        self.assertTrue(self.extractor.chapter.fullmatch('пункт        1.'))
        self.assertTrue(self.extractor.chapter.fullmatch('параграф 1.0.234.345.456'))
        self.assertTrue(self.extractor.chapter.fullmatch('глава 1'))
        self.assertTrue(self.extractor.chapter.fullmatch('определение         \t  1.4.5.6'))
        self.assertTrue(self.extractor.chapter.fullmatch('определение1.'))
        self.assertTrue(self.extractor.chapter.fullmatch('определение') is None)

    def test_dotted_num_regexp(self) -> None:
        self.assertTrue(self.extractor.dotted_num.fullmatch('1.'))
        self.assertTrue(self.extractor.dotted_num.fullmatch('12345. '))
        self.assertTrue(self.extractor.dotted_num.fullmatch('23456.2345'))
        self.assertTrue(self.extractor.dotted_num.fullmatch('1.2.34.567.'))
        self.assertTrue(self.extractor.dotted_num.fullmatch('1') is None)
        self.assertTrue(self.extractor.dotted_num.fullmatch('23456.2345d') is None)

    def test_bracket_num_regexp(self) -> None:
        self.assertTrue(self.extractor.bracket_num.fullmatch('1)'))
        self.assertTrue(self.extractor.bracket_num.fullmatch('12345678654356765)'))
        self.assertTrue(self.extractor.bracket_num.fullmatch('1') is None)
        self.assertTrue(self.extractor.bracket_num.fullmatch('1.') is None)
        self.assertTrue(self.extractor.bracket_num.fullmatch('1.2.3.4)') is None)

    def test_letter_regexp(self) -> None:
        self.assertTrue(self.extractor.letter.fullmatch('a)'))
        self.assertTrue(self.extractor.letter.fullmatch('b)'))
        self.assertTrue(self.extractor.letter.fullmatch('я)'))
        self.assertTrue(self.extractor.letter.fullmatch('г)'))
        self.assertTrue(self.extractor.letter.fullmatch('Z)') is None)
        self.assertTrue(self.extractor.letter.fullmatch('zzz)') is None)
        self.assertTrue(self.extractor.letter.fullmatch('z') is None)
