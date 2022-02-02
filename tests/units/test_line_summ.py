import unittest
from typing import List

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.examples.create_unstructured_document import hierarchy_level
from dedoc.structure_parser.heirarchy_level import HierarchyLevel


def _make_line(line: str, annotations: List[Annotation]) -> LineWithMeta:
    meta = ParagraphMetadata(paragraph_type="raw_text", predicted_classes=None, page_id=0, line_id=0)
    line = LineWithMeta(line=line, hierarchy_level=None, metadata=meta, annotations=annotations)
    return line


class TestLineSplit(unittest.TestCase):

    empty = _make_line("", [])
    italic_line = _make_line("italic", [ItalicAnnotation(0, 6, "True")])
    bold_line = _make_line("bold", [BoldAnnotation(0, 4, "True")])
    sized_line = _make_line("SmallBig", [SizeAnnotation(0, 5, "8"), SizeAnnotation(5, 8, "14")])
    lines = [empty, italic_line, sized_line, bold_line]

    def test_empty_plus_empty(self) -> None:
        result = self.empty + self.empty
        self.assertEqual("", result.line)

    def test_empty_nonempty(self) -> None:
        for non_empty in self.lines:
            for result in (self.empty + non_empty, non_empty + self.empty):
                self.assertEqual(non_empty.line, result.line)
                self.assertEqual(non_empty.annotations, result.annotations)

    def test_sum_with_str(self) -> None:
        text = "some text"
        for line in self.lines:
            result = line + text
            self.assertEqual(line.line + text, result.line)
            self.assertEqual(line.annotations, result.annotations)

    def test_line_plus_line(self) -> None:
        for first in self.lines:
            for second in self.lines:
                result = first + second
                self.assertEqual(first.line + second.line, result.line)

        result = self.bold_line + self.bold_line
        self.assertEqual([BoldAnnotation(0, len(result.line), "True")], result.annotations)

        result = self.bold_line + self.italic_line
        expected = [BoldAnnotation(0, len(self.bold_line.line), "True"), ItalicAnnotation(4, 10, "True")]
        self.assertEqual(expected, result.annotations)
