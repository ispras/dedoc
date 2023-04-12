import unittest

from dedoc.data_structures.hierarchy_level import HierarchyLevel


class TestHierarchyLevel(unittest.TestCase):

    def test_two_raw_text(self) -> None:
        h1 = HierarchyLevel.create_raw_text()
        h2 = HierarchyLevel.create_raw_text()
        h3 = HierarchyLevel(level_1=1, level_2=2, can_be_multiline=False, line_type=HierarchyLevel.raw_text)
        self.assertTrue(h1 == h2)
        self.assertTrue(h1 >= h2)
        self.assertTrue(h1 <= h2)
        self.assertTrue(h1 == h3)
        self.assertTrue(h1 >= h3)
        self.assertTrue(h1 <= h3)

    def test_raw_text_greater_than_any_other(self) -> None:
        list_item = HierarchyLevel(level_1=2, level_2=1, can_be_multiline=False, line_type=HierarchyLevel.list_item)
        raw_text = HierarchyLevel.create_raw_text()
        self.assertFalse(list_item > raw_text)
        self.assertFalse(list_item >= raw_text)
        self.assertFalse(list_item == raw_text)
        self.assertTrue(list_item < raw_text)
        self.assertTrue(list_item <= raw_text)

    def test_one_greater_than_other_level1(self) -> None:
        h1 = HierarchyLevel(level_1=2, level_2=2, can_be_multiline=False, line_type=HierarchyLevel.list_item)
        h2 = HierarchyLevel(level_1=3, level_2=1, can_be_multiline=False, line_type=HierarchyLevel.list_item)
        self.assertTrue(h1 < h2)
        self.assertTrue(h1 <= h2)
        self.assertFalse(h1 > h2)
        self.assertFalse(h1 >= h2)
        self.assertFalse(h1 == h2)

    def test_one_greater_than_other_level2(self) -> None:
        h1 = HierarchyLevel(level_1=2, level_2=1, can_be_multiline=False, line_type=HierarchyLevel.list_item)
        h2 = HierarchyLevel(level_1=2, level_2=2, can_be_multiline=False, line_type=HierarchyLevel.list_item)
        self.assertTrue(h1 < h2)
        self.assertTrue(h1 <= h2)
        self.assertFalse(h1 > h2)
        self.assertFalse(h1 >= h2)
        self.assertFalse(h1 == h2)

    def test_equal(self) -> None:
        h1 = HierarchyLevel(level_1=3, level_2=3, can_be_multiline=True, line_type=HierarchyLevel.header)
        h2 = HierarchyLevel(level_1=3, level_2=3, can_be_multiline=True, line_type=HierarchyLevel.header)
        h3 = HierarchyLevel(level_1=None, level_2=None, can_be_multiline=True, line_type=HierarchyLevel.unknown)
        h4 = HierarchyLevel(level_1=None, level_2=None, can_be_multiline=True, line_type=HierarchyLevel.unknown)
        self.assertFalse(h1 < h2)
        self.assertTrue(h1 <= h2)
        self.assertFalse(h1 > h2)
        self.assertTrue(h1 >= h2)
        self.assertTrue(h1 == h2)
        self.assertEqual(h3, h4)
        self.assertNotEqual(h1, h3)
