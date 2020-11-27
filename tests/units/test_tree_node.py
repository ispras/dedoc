import unittest
from typing import List, Set, Tuple

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.tree_node import TreeNode


class TestTreeNode(unittest.TestCase):

    def merge(self, annotations: List[Annotation]) -> Set[Tuple[int, int, str]]:
        res = TreeNode._merge_annotations(annotations)
        return {(annotation.start, annotation.end, annotation.name, annotation.value) for annotation in res}

    def test_annotation_merge_same_value(self):
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations))

    def test_annotation_merge_same_value2(self):
        annotations = [Annotation(start=4, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        self.assertSetEqual({(4, 15, "size", "1")}, self.merge(annotations))

    def test_annotation_unmerge_same_value(self):
        annotations = [Annotation(start=0, end=4, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        self.assertSetEqual({(0, 4, "size", "1"), (5, 15, "size", "1")}, self.merge(annotations))

    def test_annotation_merge_different_value(self):
        annotations = [Annotation(start=0, end=5, name="bold", value="True"),
                       Annotation(start=5, end=15, name="italic", value="True")]
        self.assertSetEqual({(0, 5, "bold", "True"), (5, 15, "italic", "True")}, self.merge(annotations))

    def test_annotation_merge_mixed(self):
        annotations = [Annotation(start=0, end=5, name="bold", value="True"),
                       Annotation(start=5, end=15, name="bold", value="True"),
                       Annotation(start=4, end=6, name="italic", value="True"),
                       Annotation(start=6, end=66, name="italic", value="True"),
                       ]
        self.assertSetEqual({(0, 15, "bold", "True"), (4, 66, "italic", "True")}, self.merge(annotations))
