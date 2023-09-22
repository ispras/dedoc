import os
from unittest import TestCase

from dedoc.config import get_config
from dedoc.dedoc_manager import DedocManager
from dedoc.manager_config import get_manager_config


class TestDedocManager(TestCase):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "csvs"))
    config = get_config()
    manager_config = get_manager_config(config=config)
    dedoc_manager = DedocManager(manager_config=manager_config, config=config)

    def test_parse_file(self) -> None:
        filename = "csv_tab.tsv"
        result = self.dedoc_manager.parse(os.path.join(self.path, "csv_tab.tsv"))
        cells = result.content.tables[0].cells
        self.assertEqual(filename, result.metadata.file_name)
        self.assertEqual(filename, result.metadata.file_name)
        self.assertLessEqual(["1", "2", "3"], [cell.get_text() for cell in cells[0]])
        self.assertLessEqual(["2", "1", "5"], [cell.get_text() for cell in cells[1]])
        self.assertLessEqual(["5", "3", "1"], [cell.get_text() for cell in cells[2]])

    def test_file_not_exists(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.dedoc_manager.parse("afagahcr")
