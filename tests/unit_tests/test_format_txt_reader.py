import os
from unittest import TestCase

from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.config import get_config
from tests.test_utils import get_test_config


class TestRawTextReader(TestCase):
    config = get_test_config()
    reader = RawTextReader(config=config)
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    def test_read_law(self) -> None:
        file = os.path.join(self.path, "laws", "коап_москвы_8_7_2015_utf.txt")
        uids_set = set()
        prefix = "txt_6210f1fb59150aae33a09f49c8724baf"  # это строка, содержащая хэш файла, который обратаывается ридером
        document = self.reader.read(file, None, {})
        for line in document.lines:
            self.assertNotIn(line.uid, uids_set)
            uids_set.add(line.uid)
            self.assertEqual(prefix, line.uid[:len(prefix)])  # в поле uid содержится хэш файла, в котором находитс строка, и id самой строки

    def test_read_tz(self) -> None:
        file = os.path.join(self.path, "tz", "tz.txt")
        uids_set = set()
        prefix = "txt_0e576a9e0008225ac27f961af60c0bee"
        document = self.reader.read(file, None, {})
        for line in document.lines:
            self.assertNotIn(line.uid, uids_set)
            uids_set.add(line.uid)
            self.assertEqual(prefix, line.uid[:len(prefix)])

    def test_get_lines_with_meta(self) -> None:
        file = os.path.join(self.path, "txt", "pr_17.txt")
        reader = RawTextReader(config=get_config())
        for line in reader._get_lines_with_meta(path=file, encoding="utf-8"):
            expected_uid = "txt_1a3cd561910506d56a65db1d1dcb5049_{}".format(line.metadata.line_id)
            self.assertEqual(expected_uid, line.uid)
