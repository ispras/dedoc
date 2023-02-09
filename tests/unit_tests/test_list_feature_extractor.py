from unittest import TestCase

import numpy as np
from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.structure_extractors.feature_extractors.list_features.list_features_extractor import ListFeaturesExtractor
from dedoc.structure_extractors.feature_extractors.list_features.prefix.bracket_prefix import BracketPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.dotted_prefix import DottedPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.empty_prefix import EmptyPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.letter_prefix import LetterPrefix
from dedoc.structure_extractors.feature_extractors.list_features.prefix.non_letter_prefix import NonLetterPrefix


class TestListFeatures(TestCase):
    feature_extractor = ListFeaturesExtractor()

    def _get_line_with_meta(self, text: str, indentation: int = 10) -> LineWithMeta:
        metadata = ParagraphMetadata(paragraph_type="raw_text", predicted_classes=None, page_id=0, line_id=0)
        annotations = [IndentationAnnotation(0, len(text), str(indentation))]
        return LineWithMeta(line=text, hierarchy_level=None, metadata=metadata, annotations=annotations)

    def test_bracket(self) -> None:
        line = self._get_line_with_meta("1) some text")
        self.assertEqual(BracketPrefix("1)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("2) some text")
        self.assertEqual(BracketPrefix("2)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("   3) some text")
        self.assertEqual(BracketPrefix("3)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\t3) some text")
        self.assertEqual(BracketPrefix("3)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("   3) some text")
        self.assertEqual(BracketPrefix("3)", 10), self.feature_extractor._get_prefix(line))

    def test_dotted(self) -> None:
        line = self._get_line_with_meta("1 some text")
        self.assertEqual(DottedPrefix("1", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("1. some text")
        self.assertEqual(DottedPrefix("1.", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("   3. some text")
        self.assertEqual(DottedPrefix("3.", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("   1.3. some text")
        self.assertEqual(DottedPrefix("1.3.", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\t1.3. some text")
        self.assertEqual(DottedPrefix("1.3.", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\n1.3. some text")
        self.assertEqual(DottedPrefix("1.3.", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("   1.2.3. some text")
        self.assertEqual(DottedPrefix("1.2.3.", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("   1.2.3 some text")
        self.assertEqual(DottedPrefix("1.2.3", 10), self.feature_extractor._get_prefix(line))

    def test_letter(self) -> None:
        line = self._get_line_with_meta("a) some text")
        self.assertEqual(LetterPrefix("a)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("b) some text")
        self.assertEqual(LetterPrefix("b)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta(" c) some text")
        self.assertEqual(LetterPrefix("c)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\td) some text")
        self.assertEqual(LetterPrefix("d)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\tа) some text")
        self.assertEqual(LetterPrefix("а)", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\tё) some text")
        self.assertEqual(LetterPrefix("ё)", 10), self.feature_extractor._get_prefix(line))

    def test_nonletter(self) -> None:
        line = self._get_line_with_meta("- some text")
        self.assertEqual(NonLetterPrefix("-", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("* some text")
        self.assertEqual(NonLetterPrefix("*", 10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("+ some text")
        self.assertEqual(NonLetterPrefix("+", 10), self.feature_extractor._get_prefix(line))

    def test_empty(self) -> None:
        line = self._get_line_with_meta("some text")
        self.assertEqual(EmptyPrefix(indent=10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\tsome text")
        self.assertEqual(EmptyPrefix(indent=10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta(" some text")
        self.assertEqual(EmptyPrefix(indent=10), self.feature_extractor._get_prefix(line))

        line = self._get_line_with_meta("\nsome text")
        self.assertEqual(EmptyPrefix(indent=10), self.feature_extractor._get_prefix(line))

    def test__get_window(self) -> None:
        prefixes = [BracketPrefix("{})".format(i), 1.01 * i) for i in range(0, 300)]
        doc_size = len(prefixes)
        assert doc_size == 300
        indents = np.array([prefix.indent for prefix in prefixes])
        window_0 = self.feature_extractor._get_window(indents=indents, prefixes=prefixes, line_id=0, doc_size=doc_size)
        self.assertEqual(0, len(window_0.prefix_before))
        self.assertNotIn("0)", [prefix.prefix for prefix in window_0.prefix_after])
        self.assertIn("2)", [prefix.prefix for prefix in window_0.prefix_after])

        window_12 = self.feature_extractor._get_window(indents=indents,
                                                       prefixes=prefixes,
                                                       line_id=12,
                                                       doc_size=doc_size)
        self.assertEqual(12, len(window_12.prefix_before))
        self.assertEqual(prefixes[12].prefix, "12)")
        self.assertNotIn("12)", [prefix.prefix for prefix in window_12.prefix_after])
        self.assertIn("13)", [prefix.prefix for prefix in window_12.prefix_after])

        window_299 = self.feature_extractor._get_window(indents=indents,
                                                        prefixes=prefixes,
                                                        line_id=299,
                                                        doc_size=doc_size)
        self.assertEqual(0, len(window_299.prefix_after))
        self.assertNotIn("299)", [prefix.prefix for prefix in window_12.prefix_after])
