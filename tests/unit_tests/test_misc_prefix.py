import unittest
from typing import List, Type

from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bullet_prefix import BulletPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.empty_prefix import EmptyPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.letter_prefix import LetterPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.prefix import LinePrefix


class TestPrefix(unittest.TestCase):

    valid_dotted = ["1.1", "1.1.", "1.1.2", "1.", "1"]
    valid_bracket = ["1)", "2)", "11231)", "11)"]
    valid_letter = ["a)", "b)", "c)", "z)", "у)", "ё)", "ъ)"]
    valid_non_letter = ["*", "+", "?", "-", "#"]
    invalid = ["\t", "", "aa", "some word", "1.a.2"]
    all_prefix = valid_dotted + valid_bracket + valid_letter + valid_non_letter + invalid

    def test_dotted_is_valid(self) -> None:
        self._check_if_valid(valid_prefix=self.valid_dotted, prefix_class=DottedPrefix)

    def test_bracket_is_valid(self) -> None:
        self._check_if_valid(valid_prefix=self.valid_bracket, prefix_class=BracketPrefix)

    def test_empty_is_valid(self) -> None:
        self._check_if_valid(valid_prefix=self.all_prefix, prefix_class=EmptyPrefix)

    def test_letter_is_valid(self) -> None:
        self._check_if_valid(valid_prefix=self.valid_letter, prefix_class=LetterPrefix)

    def test_non_letter_is_valid(self) -> None:
        self._check_if_valid(valid_prefix=self.valid_non_letter, prefix_class=BulletPrefix)

    def _check_if_valid(self, valid_prefix: List[str], prefix_class: Type[LinePrefix]) -> None:
        message_template = "assume `{prefix}` is {status} for {clazz} prefix"
        for prefix in self.all_prefix:
            class_name = prefix_class.__name__
            if prefix in valid_prefix:
                message = message_template.format(prefix=prefix, status="VALID", clazz=class_name)
                self.assertTrue(prefix_class.is_valid(prefix), message)
            else:
                message = message_template.format(prefix=prefix, status="INVALID", clazz=class_name)
                self.assertFalse(prefix_class.is_valid(prefix), message)

    def test_is_predecessor_mixed_type(self) -> None:
        mixed_prefix = [
            DottedPrefix("1.", 0),
            BracketPrefix("1)", 0),
            EmptyPrefix("some prefix"),
            LetterPrefix("a)", 0),
            BulletPrefix("-", 0)
        ]

        for first in mixed_prefix:
            for second in mixed_prefix:
                if first != second:
                    self.assertFalse(first.predecessor(second))
                    self.assertFalse(second.predecessor(first))

    def test_non_letter_predecessor(self) -> None:
        prefix_star_1 = BulletPrefix("*", 0)
        prefix_star_2 = BulletPrefix("*", 0)
        prefix_minus_1 = BulletPrefix("-", 0)
        prefix_minus_2 = BulletPrefix("-", 0)
        self.assertTrue(prefix_star_1.predecessor(prefix_star_2))
        self.assertTrue(prefix_star_2.predecessor(prefix_star_1))

        self.assertTrue(prefix_minus_1.predecessor(prefix_minus_2))
        self.assertTrue(prefix_minus_2.predecessor(prefix_minus_1))

        self.assertFalse(prefix_star_1.predecessor(prefix_minus_1))
        self.assertFalse(prefix_minus_1.predecessor(prefix_star_1))

    def test_bracket_predecessor(self) -> None:
        one = BracketPrefix("1)", 0)
        two = BracketPrefix("2)", 0)
        three = BracketPrefix("3)", 0)

        self._check_three_prefix(one, three, two)

    def test_letter_eng_predecessor(self) -> None:
        one = LetterPrefix("a)", 0)
        two = LetterPrefix("b)", 0)
        three = LetterPrefix("c)", 0)

        self._check_three_prefix(one, three, two)

    def test_letter_eng_capital_predecessor(self) -> None:
        one = LetterPrefix("A)", 0)
        two = LetterPrefix("B)", 0)
        three = LetterPrefix("C)", 0)

        self._check_three_prefix(one, three, two)

    def test_letter_rus_predecessor(self) -> None:
        one = LetterPrefix("а)", 0)
        two = LetterPrefix("б)", 0)
        three = LetterPrefix("в)", 0)

        self._check_three_prefix(one, three, two)

    def test_letter_rus_capital_predecessor(self) -> None:
        one = LetterPrefix("А)", 0)
        two = LetterPrefix("Б)", 0)
        three = LetterPrefix("В)", 0)

        self._check_three_prefix(one, three, two)

    def test_letter_rus_with_yo_predecessor(self) -> None:
        one = LetterPrefix("ё)", 0)
        two = LetterPrefix("ж)", 0)
        three = LetterPrefix("з)", 0)
        self._check_three_prefix(one, three, two)

    def test_letter_rus_without_yo_predecessor(self) -> None:
        one = LetterPrefix("е)", 0)
        two = LetterPrefix("ж)", 0)
        three = LetterPrefix("з)", 0)
        self._check_three_prefix(one, three, two)

    def test_letter_rus_capital_with_yo_predecessor(self) -> None:
        one = LetterPrefix("Ё)", 0)
        two = LetterPrefix("Ж)", 0)
        three = LetterPrefix("З)", 0)
        self._check_three_prefix(one, three, two)

    def test_letter_rus_capital_without_yo_predecessor(self) -> None:
        one = LetterPrefix("Е)", 0)
        two = LetterPrefix("Ж)", 0)
        three = LetterPrefix("З)", 0)
        self._check_three_prefix(one, three, two)

    def test_letter_all_predecessor(self) -> None:
        letters_lower_rus = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        letters_upper_rus = letters_lower_rus.upper()

        letters_lower_eng = "abcdefghijklmnopqrstuvwxyz"
        letters_upper_eng = "abcdefghijklmnopqrstuvwxyz"

        for letters in (letters_lower_rus, letters_upper_rus, letters_lower_eng, letters_upper_eng):
            for first, second in zip(letters[:-1], letters[1:]):
                first = LetterPrefix(first, 0)
                second = LetterPrefix(second, 0)
                self.assertTrue(second.predecessor(first), f"{first} should be predecessor of {second}")
                self.assertFalse(first.predecessor(second), f"{first} should not be predecessor of {second}")

    def _check_three_prefix(self, one: LinePrefix, three: LinePrefix, two: LinePrefix) -> None:
        self.assertTrue(two.predecessor(one))
        self.assertTrue(three.predecessor(two))
        self.assertFalse(one.predecessor(one))
        self.assertFalse(one.predecessor(two))
        self.assertFalse(one.predecessor(three))
        self.assertFalse(three.predecessor(one), f"{three} {one}")

    def test_dotted_predecessor_one_num(self) -> None:
        one = DottedPrefix("1.", 0)
        two = DottedPrefix("2.", 0)
        self.assertTrue(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.", 0)
        two = DottedPrefix("3.", 0)
        self.assertFalse(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

    def test_dotted_predecessor_two_num(self) -> None:
        one = DottedPrefix("1.1.", 0)
        two = DottedPrefix("1.2.", 0)
        self.assertTrue(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.1.", 0)
        two = DottedPrefix("1.3.", 0)
        self.assertFalse(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.1.", 0)
        two = DottedPrefix("1.1.", 0)
        self.assertFalse(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

    def test_dotted_predecessor_different_num(self) -> None:
        one = DottedPrefix("1.", 0)
        two = DottedPrefix("1.1.", 0)
        self.assertTrue(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.", 0)
        two = DottedPrefix("1.2.", 0)
        self.assertFalse(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.1.1", 0)
        two = DottedPrefix("1.2.", 0)
        self.assertTrue(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.1.2.1.2.1", 0)
        two = DottedPrefix("1.2.", 0)
        self.assertTrue(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

        one = DottedPrefix("1.2.1.", 0)
        two = DottedPrefix("1.2.1.1.1.", 0)
        self.assertFalse(two.predecessor(one))
        self.assertFalse(one.predecessor(two))

    def test_dotted_list_regexp(self) -> None:
        self.assertTrue(BulletPrefix.regexp.fullmatch(" -"))
        self.assertTrue(BulletPrefix.regexp.fullmatch("*"))
        self.assertTrue(BulletPrefix.regexp.fullmatch("     ©"))
        self.assertTrue(BulletPrefix.regexp.fullmatch("     ©   ") is None)
