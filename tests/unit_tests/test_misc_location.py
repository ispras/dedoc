import unittest

from dedocutils.data_structures import BBox

from dedoc.readers.pdf_reader.data_classes.tables.location import Location


class TestLocation(unittest.TestCase):

    def test_same_page(self) -> None:
        loc1 = Location(page_number=1, bbox=BBox(y_top_left=10, x_top_left=10, height=2, width=3))
        loc2 = Location(page_number=1, bbox=BBox(y_top_left=20, x_top_left=10, height=2, width=3))
        self.assertLess(loc1, loc2)
        loc3 = Location(page_number=1, bbox=BBox(y_top_left=20, x_top_left=5, height=2, width=3))
        self.assertLess(loc1, loc3)

    def test_other_page(self) -> None:
        loc1 = Location(page_number=0, bbox=BBox(y_top_left=20, x_top_left=10, height=2, width=3))
        loc2 = Location(page_number=1, bbox=BBox(y_top_left=10, x_top_left=10, height=2, width=3))
        self.assertLess(loc1, loc2)
        loc3 = Location(page_number=1, bbox=BBox(y_top_left=5, x_top_left=5, height=2, width=3))
        self.assertLess(loc1, loc3)
        self.assertGreater(loc2, loc3)
