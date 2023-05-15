import unittest

from dedoc.structure_extractors.feature_extractors.tz_feature_extractor import TzTextFeatures


class TestTzFeaturesExtractorRegexps(unittest.TestCase):
    extractor = TzTextFeatures()

    def test_named_item_regexp(self) -> None:
        self.assertTrue(self.extractor.named_item_regexp.fullmatch('раздел'))
        self.assertTrue(self.extractor.named_item_regexp.fullmatch('подраздел'))
        self.assertTrue(self.extractor.named_item_regexp.fullmatch('подраздел           \t        '))
        self.assertTrue(self.extractor.named_item_regexp.fullmatch('разделывать') is None)
