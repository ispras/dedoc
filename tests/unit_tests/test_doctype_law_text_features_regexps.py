import unittest

from dedoc.structure_extractors.feature_extractors.law_text_features import LawTextFeatures
from dedoc.structure_extractors.hierarchy_level_builders.utils_reg import roman_regexp


class TestLawTextFeaturesRegexps(unittest.TestCase):
    features = LawTextFeatures()

    def test_roman_regexp(self) -> None:
        self.assertTrue(roman_regexp.fullmatch("    XI. "))
        self.assertTrue(roman_regexp.fullmatch("      ") is None)
        self.assertTrue(roman_regexp.fullmatch("    XI.") is None)
        self.assertTrue(roman_regexp.fullmatch("\tIII. "))

    def test_application_beginnings_with_regexp(self) -> None:
        self.assertTrue(self.features.regexp_application_begin.fullmatch("приложение"))
        self.assertTrue(self.features.regexp_application_begin.fullmatch("Приложение"))
        self.assertTrue(self.features.regexp_application_begin.fullmatch("утверждены"))
        self.assertTrue(self.features.regexp_application_begin.fullmatch("приложение к приказу"))
        self.assertTrue(self.features.regexp_application_begin.fullmatch("приложение к постановлению"))
        self.assertTrue(self.features.regexp_application_begin.fullmatch("постановление") is None)
        self.assertTrue(self.features.regexp_application_begin.fullmatch("к приказу") is None)

    def test_chapter_beginnings(self) -> None:
        # note to rewrites this test if we change the num of regexps
        self.assertEqual(1, len(LawTextFeatures.named_regexp))

        regexp = LawTextFeatures.named_regexp[0]

        lines = [
            "глава v. международное сотрудничество российской\n",
            "глава vi. ответственность за нарушение\n",
            "глава 17. вступление в силу настоящего федерального закона\n",
            "глава 1. общие положения\n",
            "глава 9. финансирование в области\n",
            "глава 10. заключительные и переходные положения\n",
            "глава 7. государственное регулирование внешнеторговой\n",
            "глава 8. особые виды |\n",
            "глава 2. принципы и условия обработки персональных данных\n"
        ]
        for line in lines:
            self.assertTrue(regexp.match(line), f"doesn't match on\n ''{line}''")
