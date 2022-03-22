import os
from unittest import TestCase

from dedoc.readers.csv_reader.csv_reader import CSVReader
from dedoc.structure_constructor.table_patcher import TablePatcher


class TestTxtReader(TestCase):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "csvs"))

    def test__get_lines_with_meta(self) -> None:
        file = os.path.join(self.path, "books_2.csv")
        reader = CSVReader()
        document = reader.read(path=file, parameters={}, document_type=None)
        inserted_table = TablePatcher().insert_table(document)
        self.assertEqual(111, len(inserted_table.lines))
        inserted_table_two_times = TablePatcher().insert_table(inserted_table)
        self.assertEqual(111, len(inserted_table_two_times.lines))
