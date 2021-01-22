import unittest
from typing import List, Set, Tuple

from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.tree_node import TreeNode


class TestTreeNode(unittest.TestCase):

    def merge(self, annotations: List[Annotation], text: str) -> Set[Tuple[int, int, str]]:
        res = TreeNode._merge_annotations(annotations, text)
        return {(annotation.start, annotation.end, annotation.name, annotation.value) for annotation in res}

    def test_annotation_merge_same_value(self):
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value2(self):
        annotations = [Annotation(start=4, end=5, name="size", value="1"),
                       Annotation(start=5, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(4, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_same_value_separating_by_space(self):
        annotations = [Annotation(start=0, end=5, name="size", value="1"),
                       Annotation(start=6, end=15, name="size", value="1")]
        text = "hello my friend"
        self.assertSetEqual({(0, 15, "size", "1")}, self.merge(annotations, text))

    def test_annotation_merge_different_value(self):
        annotations = [Annotation(start=0, end=5, name="bold", value="True"),
                       Annotation(start=5, end=15, name="italic", value="True")]
        text = "hello my friend"
        self.assertSetEqual({(0, 5, "bold", "True"), (5, 15, "italic", "True")}, self.merge(annotations, text))

    def test_annotation_merge_mixed(self):
        annotations = [Annotation(start=0, end=5, name="bold", value="True"),
                       Annotation(start=5, end=15, name="bold", value="True"),
                       Annotation(start=4, end=6, name="italic", value="True"),
                       Annotation(start=6, end=66, name="italic", value="True"),
                       ]
        text = "hello my friend, hello my friend, hello my friend, hello my friend"
        self.assertSetEqual({(0, 15, "bold", "True"), (4, 66, "italic", "True")}, self.merge(annotations, text))
