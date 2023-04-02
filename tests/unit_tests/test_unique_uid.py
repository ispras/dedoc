import os
import unittest
from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.html_reader.html_reader import HtmlReader
from tests.test_utils import get_test_config


class TestUniqueUid(unittest.TestCase):

    config = get_test_config()

    def _is_unique_uids(self, lines: List[LineWithMeta]) -> bool:
        uids = set()

        for line in lines:
            if line.uid in uids:
                return False

            uids.add(line.uid)

        return True

    def test_html_unique_uids(self) -> None:
        any_doc_reader = HtmlReader(config=get_test_config())
        path = os.path.join(os.path.dirname(__file__), "../data/laws/doc_Правовые акты_0A1B19DB-15D0-47BC-B559-76DA41A36105_27.html")
        result = any_doc_reader.read(path)
        self.assertTrue(self._is_unique_uids(result.lines))
