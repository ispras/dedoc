import unittest

from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import regexps_item, regexps_item_with_bracket, regexps_subitem_with_dots, \
    regexps_subitem_extended, regexps_subitem, regexps_number, regexps_year, regexps_ends_of_number


class TestUtilsRegexps(unittest.TestCase):
    def test_item_regexp(self) -> None:
        self.assertTrue(regexps_item.match('     1. some test text'))
        self.assertIsNone(regexps_item.match('     1.1 some test text'))
        self.assertTrue(regexps_item.match('\t1.qwe') is None)
        self.assertTrue(regexps_item.match('\t5. qwe'))
        self.assertTrue(regexps_item.match('1) somw text') is None)
        self.assertTrue(regexps_item.match('edber 1) somw text') is None)

    def test_item_with_bracket_regexp(self) -> None:
        self.assertTrue(regexps_item_with_bracket.match('     1. some test text') is None)
        self.assertTrue(regexps_item_with_bracket.match('     1) some test text'))
        self.assertTrue(regexps_item_with_bracket.match(' \t   1} some test text'))
        self.assertTrue(regexps_item_with_bracket.match(' \t   4.2.3.4) some test text'))
        self.assertTrue(regexps_item_with_bracket.match(' \t   4.234) some test text'))
        self.assertTrue(regexps_item_with_bracket.match('  dkjfbe    1. some test text') is None)
        self.assertTrue(regexps_item_with_bracket.match('123|') is None)

    def test_subitem_with_dots_regexp(self) -> None:
        self.assertTrue(regexps_subitem_with_dots.match('а) текст на русском'))
        self.assertTrue(regexps_subitem_with_dots.match('      123.я.  '))
        self.assertTrue(regexps_subitem_with_dots.match('      123.т.е.с.т.д.л.и.н.н.о.г.о.с.п.и.с.к.а.  '))
        self.assertTrue(regexps_subitem_with_dots.match('    123.456') is None)
        self.assertTrue(regexps_subitem_with_dots.match('      123.ч.и.с.123.л.а.  '))
        self.assertTrue(regexps_subitem_with_dots.match('12.б.у.к.в.ы. '))
        self.assertTrue(regexps_subitem_with_dots.match('23.б.у.к.в.ы.') is None)
        self.assertTrue(regexps_subitem_with_dots.match('      123.ч.и.с.123.ла.  ') is None)
        self.assertTrue(regexps_subitem.match('б)'))
        self.assertTrue(regexps_subitem.match('b)') is None)

    def test_subitem_extended_regexp(self) -> None:
        self.assertTrue(regexps_subitem_extended.fullmatch('z)'))
        self.assertTrue(regexps_subitem_extended.fullmatch('я}'))
        self.assertTrue(regexps_subitem_extended.fullmatch('Q|') is None)

    def test_subitem_regexp(self) -> None:
        self.assertTrue(regexps_subitem.match('а) текст на русском'))
        self.assertTrue(regexps_subitem.match('    ё) english text'))
        self.assertTrue(regexps_subitem.match('start ё) english text') is None)
        self.assertTrue(regexps_subitem.match('b)') is None)
        self.assertTrue(regexps_subitem.match('б)'))
        self.assertTrue(regexps_subitem.match('б|') is None)

    def test_number_regexp(self) -> None:
        self.assertTrue(regexps_number.match('3. '))
        self.assertTrue(regexps_number.match('3.') is None)
        self.assertTrue(regexps_number.match('   3.ф oksdfnn'))
        self.assertTrue(regexps_number.match('\t12'))
        self.assertTrue(regexps_number.match('123') is None)
        self.assertTrue(regexps_number.match('12.34.56.78'))
        self.assertTrue(regexps_number.match('12.3.4.5.6.7.8)'))
        self.assertTrue(regexps_number.match('12.34}'))
        self.assertTrue(regexps_number.match('1.23.4.Z'))
        self.assertTrue(regexps_number.match('lorem ipsum 12') is None)

    def test_ends_of_number_regexp(self) -> None:
        self.assertTrue(regexps_ends_of_number.fullmatch('ё'))
        self.assertTrue(regexps_ends_of_number.fullmatch('       '))
        self.assertTrue(regexps_ends_of_number.fullmatch(''))
        self.assertTrue(regexps_ends_of_number.fullmatch('abacaba') is None)
        self.assertTrue(regexps_ends_of_number.fullmatch('z'))

    def test_year_regexp(self) -> None:
        self.assertTrue(regexps_year.fullmatch('1998'))
        self.assertTrue(regexps_year.fullmatch('1900'))
        self.assertTrue(regexps_year.fullmatch('2000'))
        self.assertTrue(regexps_year.fullmatch('2021'))
        self.assertTrue(regexps_year.fullmatch('2099'))
