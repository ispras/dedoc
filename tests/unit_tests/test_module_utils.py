import unittest

from dedoc.utils.utils import splitext_


class TestUtils(unittest.TestCase):

    def test_splitext_simple_name(self) -> None:
        name_extension = "name.doc"
        name, extension = splitext_(name_extension)
        self.assertEqual("name", name)
        self.assertEqual(".doc", extension)

    def test_splitext_apostrophe_name(self) -> None:
        name_extension = "Well. Known -Nik O'Tinn -Ireland 2023- DRAFT.doc"
        name, extension = splitext_(name_extension)
        self.assertEqual("Well. Known -Nik O'Tinn -Ireland 2023- DRAFT", name)
        self.assertEqual(".doc", extension)

    def test_splitext_space_name(self) -> None:
        name_extension = "some file .doc"
        name, extension = splitext_(name_extension)
        self.assertEqual("some file ", name)
        self.assertEqual(".doc", extension)

    def test_splitext_dots_name(self) -> None:
        name_extension = "1700134420_941.23_to_csv.csv"
        name, extension = splitext_(name_extension)
        self.assertEqual("1700134420_941.23_to_csv", name)
        self.assertEqual(".csv", extension)

    def test_splitext_double_dot_extension(self) -> None:
        name_extension = "some_name.tar.gz"
        name, extension = splitext_(name_extension)
        self.assertEqual("some_name", name)
        self.assertEqual(".tar.gz", extension)
