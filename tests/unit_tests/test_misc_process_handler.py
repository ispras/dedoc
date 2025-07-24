import logging
import os
import tempfile
from unittest import IsolatedAsyncioTestCase

from dedoc.api.process_handler import ProcessHandler


class TestProcessHandler(IsolatedAsyncioTestCase):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "csvs"))
    process_handler = ProcessHandler(logger=logging.getLogger())

    async def test_handle_file(self) -> None:
        filename = "csv_tab.tsv"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await self.process_handler.handle(None, {}, os.path.join(self.path, filename), tmpdir)
        cells = result.content.tables[0].cells
        self.assertEqual(filename, result.metadata.file_name)
        self.assertLessEqual(["1", "2", "3"], ["".join([line.text for line in cell.lines]) for cell in cells[0]])

    async def test_file_not_exists(self) -> None:
        with self.assertRaises(FileNotFoundError):
            with tempfile.TemporaryDirectory() as tmpdir:
                _ = await self.process_handler.handle(None, {}, "afagahcr", tmpdir)
