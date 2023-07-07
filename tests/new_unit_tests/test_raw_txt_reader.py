import os
from unittest import TestCase

from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from tests.test_utils import get_test_config

# на законы и тз в txt формате
# проверить, что такое префикс
# выделить группы тестов
# скинуть в новую подпапку отрефакторенные тесты
# удалять дублирующиеся тесты

class TestRawTextReader(TestCase):
    """
    Class with implemented tests for raw text reader
    """
    config = get_test_config()
    reader = RawTextReader(config=config)
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    def test_read_law(self) -> None:
        """
        Tests reader with law document
        """
        file = os.path.join(self.path, "laws", "коап_москвы_8_7_2015_utf.txt")
        uids_set = set()
        prefix = "txt_6210f1fb59150aae33a09f49c8724baf"  # это строка, содержащая хэш файла, который обратаывается ридером
        document = self.reader.read(file, None, {})
        for line in document.lines:
            self.assertNotIn(line.uid, uids_set)
            uids_set.add(line.uid)
            self.assertEqual(prefix, line.uid[:len(prefix)])  # в поле uid содержится хэш файла, в котором находитс строка, и id самой строки

    def test_read_tz(self) -> None:
        """
        Tests reader with tz document
        """
        file = os.path.join(self.path, "tz", "tz.txt")
        uids_set = set()
        prefix = "txt_0e576a9e0008225ac27f961af60c0bee"
        document = self.reader.read(file, None, {})
        for line in document.lines:
            self.assertNotIn(line.uid, uids_set)
            uids_set.add(line.uid)
            self.assertEqual(prefix, line.uid[:len(prefix)])
