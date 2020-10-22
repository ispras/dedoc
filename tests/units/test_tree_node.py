import unittest
from typing import List, Set, Tuple

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.tree_node import TreeNode


class TestTreeNode(unittest.TestCase):

    def merge(self, annotations: List[Annotation]) -> Set[Tuple[int, int, str]]:
        res = TreeNode._merge_annotations(annotations)
        return {(annotation.start, annotation.end, annotation.value) for annotation in res}

    def test_annotation_merge_same_value(self):
        annotations = [Annotation(start=0, end=5, value="A"), Annotation(start=5, end=15, value="A")]
        self.assertSetEqual({(0, 15, "A")}, self.merge(annotations))

    def test_annotation_merge_same_value2(self):
        annotations = [Annotation(start=4, end=5, value="A"), Annotation(start=5, end=15, value="A")]
        self.assertSetEqual({(4, 15, "A")}, self.merge(annotations))

    def test_annotation_unmerge_same_value(self):
        annotations = [Annotation(start=0, end=4, value="A"), Annotation(start=5, end=15, value="A")]
        self.assertSetEqual({(0, 4, "A"), (5, 15, "A")}, self.merge(annotations))

    def test_annotation_merge_different_value(self):
        annotations = [Annotation(start=0, end=5, value="A"), Annotation(start=5, end=15, value="B")]
        self.assertSetEqual({(0, 5, "A"), (5, 15, "B")}, self.merge(annotations))

    def test_annotation_merge_mixed(self):
        annotations = [Annotation(start=0, end=5, value="A"), Annotation(start=5, end=15, value="A"),
                       Annotation(start=4, end=6, value="B"), Annotation(start=6, end=66, value="B"),
                       ]
        self.assertSetEqual({(0, 15, "A"), (4, 66, "B")}, self.merge(annotations))
