import unittest
from typing import List, Set, Tuple

from dedoc.data_structures import Annotation
from dedoc.structure_constructor import AnnotationMerger
from tests.test_utils import TestTimeout


class TestAnnotationMerger(unittest.TestCase):

    def merge(self, annotations: List[Annotation], text: str) -> Set[Tuple[int, int, str]]:
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
        annotations = [Annotation(start=0, end=5, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 5, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_included(self) -> None:
        annotations = [Annotation(start=0, end=15, name="size", value="1"),
                       Annotation(start=3, end=5, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value2(self) -> None:
        annotations = [Annotation(start=4, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(4, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_space(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=6, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_tab(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=6, end=15, name="size", value="1")]
        text = "hello\tmy friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_newline(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=6, end=15, name="size", value="1")]
        text = "hello\nmy friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_no_spaces(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        text = "hellomyfriend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_many_space(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=20, end=25, name="size", value="1")]
        text = "hello               my friend"
        self.assertSetEqual({(0, 25, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_many_space_end_space(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=20, end=25, name="size", value="1")]
        text = "hello               my friend      "
        self.assertSetEqual({(0, 25, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_annotations(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=6, end=10, name="size", value="1"),
                       Annotation(start=10, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_nested_annotations(self) -> None:
        annotations = [Annotation(start=0, end=15, name="size", value="1"),
                       Annotation(start=6, end=10, name="size", value="1"),
                       Annotation(start=3, end=8, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_intersected_annotations(self) -> None:
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=3, end=8, name="size", value="1"),
                       Annotation(start=6, end=9, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 9, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_three_one_intersected_annotations(self) -> None:
        annotations = [Annotation(start=0, end=3, name="size", value="1"),
                       Annotation(start=3, end=6, name="size", value="1"),
                       Annotation(start=8, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 6, "size", "1"), (8, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_different_value(self) -> None:
        annotations = [Annotation(start=0, end=5, name="bold", value="True"),
                       Annotation(start=5, end=15, name="italic", value="True")]
        text = "hello my friend"
        self.assertSetEqual({(0, 5, "bold", "True"), (5, 15, "italic", "True")}, self.merge(annotations, text))

    def test_annotation_merge_mixed(self) -> None:
        annotations = [Annotation(start=0, end=5, name="bold", value="True"),
                       Annotation(start=5, end=15, name="bold", value="True"),
                       Annotation(start=4, end=6, name="italic", value="True"),
                       Annotation(start=6, end=66, name="italic", value="True"),
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
