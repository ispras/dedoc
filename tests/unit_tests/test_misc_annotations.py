import unittest
from typing import List, Set, Tuple

from dedoc.data_structures.annotation import Annotation
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.utils.annotation_merger import AnnotationMerger
from tests.test_utils import TestTimeout


class TestAnnotationMerger(unittest.TestCase):
    def merge(self, annotations: List[Annotation], text: str) -> Set[Tuple[int, int, str, str]]:
        res = AnnotationMerger().merge_annotations(annotations, text)
        return {(annotation.start, annotation.end, annotation.name, annotation.value) for annotation in res}

    def test_annotation_merge_zero(self) -> None:
        annotations = []
        text = "hello my friend"
        self.assertSetEqual(set(), self.merge(annotations, text))

    def test_annotation_merge_one(self) -> None:
        annotations = [Annotation(start=0, end=4, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 4, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_one_near_space(self) -> None:
        """
        Tests the case where the end of annotation lands on a space symbol
        """
        annotations = [Annotation(start=0, end=5, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 5, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"), Annotation(start=5, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_no_spaces(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"), Annotation(start=5, end=15, name="size", value="1")]
        text = "hellomyfriend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_many_space(self) -> None:
        """
        Tests the case where two annotations are separated by many spaces with no spaces at the end
        """
        annotations = [Annotation(start=0, end=5, name="size", value="1"), Annotation(start=20, end=25, name="size", value="1")]
        text = "hello               my friend"
        self.assertSetEqual({(0, 25, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_many_space_end_space(self) -> None:
        """
        Tests the case where two annotations are separated by many spaces with many spaces at te end
        """
        annotations = [Annotation(start=0, end=5, name="size", value="1"), Annotation(start=20, end=25, name="size", value="1")]
        text = "hello               my friend      "
        self.assertSetEqual({(0, 25, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_space(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"), Annotation(start=6, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_tab(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"), Annotation(start=6, end=15, name="size", value="1")]
        text = "hello\tmy friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_newline(self) -> None:
        annotations = [
            Annotation(start=0, end=5, name="size", value="1"),
            Annotation(start=6, end=15, name="size", value="1")
        ]
        text = "hello\nmy friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_included(self) -> None:
        """
        Tests the case where one annotation includes another. Both annotations share the same name and value
        """
        annotations = [
            Annotation(start=0, end=15, name="size", value="1"),
            Annotation(start=3, end=5, name="size", value="1")
        ]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_annotations(self) -> None:
        annotations = [
            Annotation(start=0, end=5, name="size", value="1"),
            Annotation(start=6, end=10, name="size", value="1"),
            Annotation(start=10, end=15, name="size", value="1")
        ]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_nested_annotations(self) -> None:
        annotations = [
            Annotation(start=0, end=15, name="size", value="1"),
            Annotation(start=6, end=10, name="size", value="1"),
            Annotation(start=3, end=8, name="size", value="1")
        ]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_intersected_annotations(self) -> None:
        annotations = [
            Annotation(start=0, end=5, name="size", value="1"),
            Annotation(start=3, end=8, name="size", value="1"),
            Annotation(start=6, end=9, name="size", value="1")
        ]
        text = "hello my friend"
        self.assertSetEqual({(0, 9, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_one_intersected_annotations(self) -> None:
        annotations = [
            Annotation(start=0, end=3, name="size", value="1"),
            Annotation(start=3, end=6, name="size", value="1"),
            Annotation(start=8, end=15, name="size", value="1")
        ]
        text = "hello my friend"
        self.assertSetEqual({(0, 6, "size", "1"), (8, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_different_value(self) -> None:
        annotations = [
            Annotation(start=0, end=5, name="bold", value="True"),
            Annotation(start=5, end=15, name="italic", value="True")
        ]
        text = "hello my friend"
        self.assertSetEqual({(0, 5, "bold", "True"), (5, 15, "italic", "True")}, self.merge(annotations, text))

    def test_annotation_merge_mixed(self) -> None:
        annotations = [
            Annotation(start=0, end=5, name="bold", value="True"),
            Annotation(start=5, end=15, name="bold", value="True"),
            Annotation(start=4, end=6, name="italic", value="True"),
            Annotation(start=6, end=66, name="italic", value="True")
        ]
        text = "hello my friend, hello my friend, hello my friend, hello my friend"
        self.assertSetEqual({(0, 15, "bold", "True"), (4, 66, "italic", "True")}, self.merge(annotations, text))

    def test_merge_1000_annotations(self) -> None:
        timeout = 10
        n = 1000
        annotations = [Annotation(start=i, end=i + 1, name="bold", value="True") for i in range(n)]
        text = "x" * n
        with TestTimeout(timeout):
            result = self.merge(annotations, text)
        self.assertSetEqual({(0, n, "bold", "True")}, result)

    def test_merge_1000_pair_annotations(self) -> None:
        timeout = 10
        n = 1000
        annotations = []
        for i in range(n):
            annotations.append(Annotation(start=i, end=i + 1, name="bold", value="True"))
            annotations.append(Annotation(start=i, end=i + 1, name="size", value="1"))

        text = "x" * n
        with TestTimeout(timeout):
            result = self.merge(annotations, text)
        self.assertSetEqual({(0, n, "bold", "True"), (0, n, "size", "1")}, result)

    def test_merge_1000_no_intersection(self) -> None:
        timeout = 10
        n = 1000
        annotations = []
        for i in range(0, n, 2):
            annotations.append(Annotation(start=i, end=i + 1, name="bold", value="True"))

        text = "x" * (2 * n)
        with TestTimeout(timeout):
            result = self.merge(annotations, text)
        self.assertSetEqual({(a.start, a.end, a.name, a.value) for a in annotations}, result)

    def test_merge_space(self) -> None:
        annotations = [
            Annotation(start=0, end=6, name="size", value="12.0"),
            Annotation(start=7, end=11, name="size", value="12.0"),
            Annotation(start=6, end=7, name="size", value="1"),
            Annotation(start=6, end=7, name="bold", value="True")
        ]
        text = "normal text"
        result = self.merge(annotations, text)
        self.assertEqual(2, len(result))
        self.assertIn((0, 11, "size", "12.0"), result)
        self.assertIn((6, 7, "bold", "True"), result)

    def test_merge_only_spaces(self) -> None:
        annotations = [
            Annotation(start=0, end=1, name="size", value="12.0"),
            Annotation(start=0, end=1, name="bold", value="True"),
            Annotation(start=1, end=2, name="italic", value="True"),
            Annotation(start=2, end=3, name="bold", value="False"),
            Annotation(start=3, end=4, name="size", value="1"),
            Annotation(start=4, end=5, name="size", value="5")
        ]
        text = " \t \t\n"
        result = self.merge(annotations, text)
        self.assertEqual(6, len(result))
        actual_result = {(ann.start, ann.end, ann.name, ann.value) for ann in annotations}
        self.assertSetEqual(actual_result, result)


class TestAbstractStructureExtractor(unittest.TestCase):
    def test_annotation_extractor_left(self) -> None:
        """
        Tests the case where extraction region is one pixel to the left of the annotation region
        """
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 0, 2)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].value, annotations[0].value)
        self.assertEqual(res[0].start, annotations[0].start)
        self.assertEqual(res[0].end, 2)

    def test_annotation_extractor_right(self) -> None:
        """
        Tests the case where extraction region is one character to the right of the annotation region
        """
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 2, 3)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].value, annotations[0].value)
        self.assertEqual(res[0].start, 0)
        self.assertEqual(res[0].end, 1)

    def test_annotation_extractor_skip_all(self) -> None:
        """
        Tests the case where extraction and annotation regions do not intersect
        """
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 4, 5)
        self.assertEqual(len(res), 0)

    def test_annotation_extractor_select_one(self) -> None:
        """
        Tests the case where extraction region contains only one character
        """
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 3, 3)
        self.assertEqual(len(res), 0)

    def test_annotation_extractor_multiple(self) -> None:
        """
        Tests the case with extracting two annotations from one region
        """
        annotations = [Annotation(1, 3, name="bold", value="True"), Annotation(2, 5, name="italic", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 1, 4)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].value, annotations[0].value)
        self.assertEqual(res[0].name, annotations[0].name)
        self.assertEqual(res[0].start, 0)
        self.assertEqual(res[0].end, 2)

        self.assertEqual(res[1].value, annotations[1].value)
        self.assertEqual(res[1].name, annotations[1].name)
        self.assertEqual(res[1].start, 1)
        self.assertEqual(res[1].end, 3)

    def test_annotation_extractor_zero(self) -> None:
        annotations = []
        res = AbstractStructureExtractor._select_annotations(annotations, 1, 4)
        self.assertEqual(len(res), 0)
