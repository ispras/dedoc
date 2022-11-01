import unittest
from typing import List

from src.data_structures.annotation import Annotation
from src.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from src.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from src.data_structures.line_with_meta import LineWithMeta
from src.data_structures.paragraph_metadata import ParagraphMetadata
from src.structure_parser.heirarchy_level import HierarchyLevel


class TestLineSplit(unittest.TestCase):

    def test_empty_line_slice(self) -> None:
        line = self._get_line("", [])
        with self.assertRaises(IndexError):
            _ = line[0]
        line_slice = line[0:]
        self.assertNotEqual(id(line_slice), id(line))
        self.assertEqual(line_slice.line, line.line)
        self.assertEqual(line_slice.annotations, line.annotations)

    def test_line_slice_one_index(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[7]
        self.assertEqual("t", line_slice.line)
        self.assertEqual(2, len(line_slice.annotations))
        self.assertIn(BoldAnnotation(0, 1, "False"), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 1, "10"), line_slice.annotations)

    def test_line_slice_one_negative_index(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[-5]
        self.assertEqual(1, len(line_slice))
        self.assertEqual("E", line_slice.line)
        self.assertEqual(2, len(line_slice.annotations))
        self.assertIn(BoldAnnotation(0, 1, "False"), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 1, "14"), line_slice.annotations)
        with self.assertRaises(IndexError):
            _ = line[-9]
        with self.assertRaises(IndexError):
            _ = line[-10]
        for index in range(-len(line), len(line)):
            slice_left = line[index]
            slice_right = line[index % len(line)]
            self.assertEqual(slice_left.line, slice_right.line)

    def test_line_slice_border_left(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[0:4]
        self.assertEqual("SOME", line_slice.line)
        self.assertEqual(2, len(line_slice.annotations), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 4, "14"), line_slice.annotations)
        self.assertIn(BoldAnnotation(0, 4, "False"), line_slice.annotations)

    def test_line_slice_border_right(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[4:8]
        self.assertEqual("text", line_slice.line)
        self.assertEqual(2, len(line_slice.annotations), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 4, "10"), line_slice.annotations)
        self.assertIn(BoldAnnotation(0, 4, "False"), line_slice.annotations)

    def test_line_slice_intersection(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[3:8]
        self.assertEqual("Etext", line_slice.line)
        self.assertEqual(3, len(line_slice.annotations), line_slice.annotations)
        self.assertIn(SizeAnnotation(1, 5, "10"), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 1, "14"), line_slice.annotations)
        self.assertIn(BoldAnnotation(0, 5, "False"), line_slice.annotations)

    def test_line_slice_type_error(self) -> None:
        line = self._get_line_for_slice()
        for index in ["f", None, 1.3]:
            with self.assertRaises(TypeError):
                _ = line[index]

    def test_line_slice_out_of_range(self) -> None:
        line = self._get_line_for_slice()
        with self.assertRaises(IndexError):
            _ = line[9]
        with self.assertRaises(IndexError):
            _ = line[8]
        with self.assertRaises(IndexError):
            _ = line[8:]
        with self.assertRaises(IndexError):
            _ = line[9:]

    def test_line_slice_border(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[4:8]
        self.assertIn(BoldAnnotation(0, 4, "False"), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 4, "10"), line_slice.annotations)
        self.assertEqual(2, len(line_slice.annotations))

    def test_not_implemented_slice(self) -> None:
        line = self._get_line_for_slice()
        with self.assertRaises(NotImplementedError):
            _ = line[1:2:3]
        with self.assertRaises(NotImplementedError):
            _ = line[-2:-1]
        with self.assertRaises(NotImplementedError):
            _ = line[1:2:-1]
        with self.assertRaises(NotImplementedError):
            _ = line[-2:-1:2]

    def test_line_slice_out_of_border(self) -> None:
        line = self._get_line_for_slice()
        line_slice = line[3:10]
        self.assertIn(BoldAnnotation(0, 5, "False"), line_slice.annotations)
        self.assertIn(SizeAnnotation(1, 5, "10"), line_slice.annotations)
        self.assertIn(SizeAnnotation(0, 1, "14"), line_slice.annotations)
        self.assertEqual(3, len(line_slice.annotations))

    def test_split_empty_line(self) -> None:
        line = self._get_line("", [])
        split = line.split("\n")
        self.assertListEqual([line], split)

    def test_split_empty_sep(self) -> None:
        line = self._get_line("some text", [BoldAnnotation(0, 3, "True")])
        with self.assertRaises(ValueError):
            line.split("")

    def test_one_element(self) -> None:
        line = self._get_line("\n", [])
        split = line.split("\n")
        self.assertListEqual([line], split)

    def test_end_with_sep(self) -> None:
        line = self._get_line("some text\n", [])
        split = line.split("\n")
        self.assertListEqual([line], split)

    def test_two_sep_in_a_row(self) -> None:
        line = self._get_line("some\n\ntext\n", [BoldAnnotation(0, 11, "True")])
        split = line.split("\n")
        self.assertEqual(3, len(split))
        left, middle, right = split
        self.assertEqual("some\n", left.line)

        self.assertEqual("\n", middle.line)

        self.assertEqual("text\n", right.line)

        self.__annotation_all_line(split)

    def test_two_symbols_sep(self) -> None:
        line = self._get_line("some--text\n", [BoldAnnotation(0, 11, "True")])
        split = line.split("--")
        self.assertEqual(2, len(split))
        left, right = split
        self.assertEqual("some--", left.line)

        self.assertEqual("text\n", right.line)
        self.assertEqual("text\n", right.line)

        self.__annotation_all_line(split)

    def test_two_sep(self) -> None:
        line = self._get_line("some\nmore\ntext", [BoldAnnotation(0, 14, "True")])
        split = line.split("\n")
        self.assertEqual(3, len(split))
        left, middle, right = split
        self.assertEqual("some\n", left.line)

        self.assertEqual("more\n", middle.line)
        self.assertEqual("text", right.line)

        self.__annotation_all_line(split)

    def test_by_regexp_sep(self) -> None:
        line = self._get_line("some more  text\twith\nspaces \t\n", [BoldAnnotation(0, 30, "True")])
        split = line.split(r"\s+")
        self.assertEqual(5, len(split))
        one, two, three, four, five = split
        self.assertEqual("some ", one.line)
        self.assertEqual("more  ", two.line)
        self.assertEqual("text\t", three.line)
        self.assertEqual("with\n", four.line)
        self.assertEqual("spaces \t\n", five.line)

        self.__annotation_all_line(split)

    def test_no_sep(self) -> None:
        line = self._get_line("some more text", [BoldAnnotation(0, 14, "True")])
        split = line.split("\n")
        self.assertListEqual([line], split)

    def test_two_annotations(self) -> None:
        line = self._get_line("some\ntext", [SizeAnnotation(0, 9, "14"), BoldAnnotation(0, 9, "True")])
        split = line.split("\n")
        self.assertEqual(2, len(split))
        for line in split:
            annotation_bold, annotation_size = sorted(line.annotations, key=lambda a: a.name)
            self.assertEqual(BoldAnnotation.name, annotation_bold.name)
            self.assertEqual("True", annotation_bold.value)
            self.assertEqual(0, annotation_bold.start)
            self.assertEqual(len(line.line), annotation_bold.end)

            self.assertEqual(SizeAnnotation.name, annotation_size.name)
            self.assertEqual("14", annotation_size.value)
            self.assertEqual(0, annotation_size.start)
            self.assertEqual(len(line.line), annotation_size.end)

    def test_two_annotations_no_intersection(self) -> None:
        line = self._get_line("some\ntext", [SizeAnnotation(0, 5, "14"), SizeAnnotation(5, 9, "10")])
        split = line.split("\n")
        self.assertEqual(2, len(split))
        for size, line in zip(("14", "10"), split):
            self.assertEqual(1, len(line.annotations))
            annotation_size = line.annotations[0]

            self.assertEqual(SizeAnnotation.name, annotation_size.name)
            self.assertEqual(size, annotation_size.value)
            self.assertEqual(0, annotation_size.start)
            self.assertEqual(len(line.line), annotation_size.end)

    def test_two_annotations_no_intersection_by_sep(self) -> None:
        line = self._get_line("some\ntext", [SizeAnnotation(4, 9, "14")])
        split = line.split("\n")
        self.assertEqual(2, len(split))
        for (start, end), line in zip(((4, 5), (0, 4)), split):
            self.assertEqual(1, len(line.annotations))
            annotation_size = line.annotations[0]

            self.assertEqual(SizeAnnotation.name, annotation_size.name)
            self.assertEqual("14", annotation_size.value)
            self.assertEqual(start, annotation_size.start)
            self.assertEqual(end, annotation_size.end)

    def test_up_to_sep(self) -> None:
        line = self._get_line("some\ntext", [SizeAnnotation(0, 5, "14")])
        split = line.split("\n")
        self.assertEqual(2, len(split))
        left, right = split
        self.assertEqual(1, len(left.annotations))
        self.assertEqual(0, len(right.annotations))

    def __annotation_all_line(self, split: List[LineWithMeta]) -> None:
        for line in split:
            annotations = line.annotations
            self.assertEqual(1, len(annotations))
            annotation = annotations[0]
            self.assertEqual(0, annotation.start)
            self.assertEqual(len(line.line), annotation.end)
            self.assertEqual("True", annotation.value)
            self.assertEqual(BoldAnnotation.name, annotation.name)

    def _get_line(self, line: str, annotations: List[Annotation]) -> LineWithMeta:
        metadata = ParagraphMetadata(paragraph_type=HierarchyLevel.raw_text,
                                     predicted_classes=None,
                                     page_id=0,
                                     line_id=1)
        line = LineWithMeta(line=line,
                            hierarchy_level=HierarchyLevel.create_raw_text(),
                            metadata=metadata,
                            annotations=annotations)
        return line

    def _get_line_for_slice(self) -> LineWithMeta:
        annotations = [
            SizeAnnotation(0, 4, "14"),
            SizeAnnotation(4, 8, "10"),
            BoldAnnotation(0, 8, "False")
        ]
        return self._get_line("SOMEtext", annotations=annotations)
