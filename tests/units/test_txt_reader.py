import os
from unittest import TestCase

from dedoc.readers.txt_reader.raw_text_reader import RawTextReader


class TestTxtReader(TestCase):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    def test__get_lines_with_meta(self):
        file = os.path.join(self.path, "pr_17.txt")
        reader = RawTextReader()
        for line in reader._get_lines_with_meta(path=file):
            expected_uid = "txt_1a3cd561910506d56a65db1d1dcb5049_{}".format(line.metadata.line_id)
            self.assertEqual(expected_uid, line.uid)
