import unittest

from dedoc.data_structures.hierarchy_level import HierarchyLevel


class TestHierarchyLevel(unittest.TestCase):

    def test_two_raw_text(self) -> None:
        h1 = HierarchyLevel.create_raw_text()
        h2 = HierarchyLevel.create_raw_text()
        h3 = HierarchyLevel(level_1=1, level_2=2, can_be_multiline=False, paragraph_type="raw_text")
        self.assertTrue(h1 == h2)
        self.assertTrue(h1 >= h2)
        self.assertTrue(h1 <= h2)
        self.assertTrue(h1 == h3)
        self.assertTrue(h1 >= h3)
        self.assertTrue(h1 <= h3)

    def test_raw_text_greater_than_any_other(self) -> None:
        list_item = HierarchyLevel(level_1=2, level_2=1, can_be_multiline=False, paragraph_type="list_item")
        raw_text = HierarchyLevel.create_raw_text()
        self.assertFalse(list_item > raw_text)
        self.assertFalse(list_item >= raw_text)
        self.assertFalse(list_item == raw_text)
        self.assertTrue(list_item < raw_text)
        self.assertTrue(list_item <= raw_text)

    def test_one_greater_than_other_level1(self) -> None:
        h1 = HierarchyLevel(level_1=2, level_2=2, can_be_multiline=False, paragraph_type="list_item")
        h2 = HierarchyLevel(level_1=3, level_2=1, can_be_multiline=False, paragraph_type="list_item")
        self.assertTrue(h1 < h2)
        self.assertTrue(h1 <= h2)
        self.assertFalse(h1 > h2)
        self.assertFalse(h1 >= h2)
        self.assertFalse(h1 == h2)

    def test_one_greater_than_other_level2(self) -> None:
        h1 = HierarchyLevel(level_1=2, level_2=1, can_be_multiline=False, paragraph_type="list_item")
        h2 = HierarchyLevel(level_1=2, level_2=2, can_be_multiline=False, paragraph_type="list_item")
        self.assertTrue(h1 < h2)
        self.assertTrue(h1 <= h2)
        self.assertFalse(h1 > h2)
        self.assertFalse(h1 >= h2)
        self.assertFalse(h1 == h2)

    def test_equal(self) -> None:
        h1 = HierarchyLevel(level_1=3, level_2=3, can_be_multiline=True, paragraph_type="header")
        h2 = HierarchyLevel(level_1=3, level_2=3, can_be_multiline=True, paragraph_type="header")
        self.assertFalse(h1 < h2)
        self.assertTrue(h1 <= h2)
        self.assertFalse(h1 > h2)
        self.assertTrue(h1 >= h2)
        self.assertTrue(h1 == h2)
