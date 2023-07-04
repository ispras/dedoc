import unittest

from dedoc.data_structures.annotation import Annotation
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor


# скорее всего annotation merger ???
# написать документацию к классам !!!
# написать комменты к функциям

class TestAbstractStructureExtractor(unittest.TestCase):

    def test_split_annotation_left(self) -> None:
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 0, 2)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].value, annotations[0].value)
        self.assertEqual(res[0].start, annotations[0].start)
        self.assertEqual(res[0].end, 2)

    def test_split_annotation_right(self) -> None:
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 2, 3)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].value, annotations[0].value)
        self.assertEqual(res[0].start, 0)
        self.assertEqual(res[0].end, 1)

    def test_split_annotation_skip_all(self) -> None:
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 4, 5)
        self.assertEqual(len(res), 0)

    def test_split_annotation_select1(self) -> None:
        annotations = [Annotation(1, 3, name="bold", value="True")]
        res = AbstractStructureExtractor._select_annotations(annotations, 3, 3)
        self.assertEqual(len(res), 0)

    def test_split_annotation_multiple(self) -> None:
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

    def test_split_annotation_0(self) -> None:
        annotations = []
        res = AbstractStructureExtractor._select_annotations(annotations, 1, 4)
        self.assertEqual(len(res), 0)
