import os
from unittest import TestCase

from dedoc.config import get_config
from dedoc.manager.dedoc_manager import DedocManager
from dedoc.manager_config import get_manager_config


class TestDedocManager(TestCase):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "csvs"))
    config = get_config()
    manager_config = get_manager_config(config=config)
    dedoc_manager = DedocManager.from_config(version="test", manager_config=manager_config, config=config)

    def test_parse_file(self):
        filename = "csv_tab.tsv"
        result = self.dedoc_manager.parse_file(os.path.join(self.path, "csv_tab.tsv"), {})
        self.assertEqual(filename, result.metadata.file_name)
        self.assertEqual(filename, result.metadata.file_name)
        self.assertLessEqual(["1", "2", "3"], result.content.tables[0].cells[0])
        self.assertLessEqual(["2", "1", "5"], result.content.tables[0].cells[1])
        self.assertLessEqual(["5", "3", "1"], result.content.tables[0].cells[2])

    def test_version(self):
        self.assertEqual("test", self.dedoc_manager.version)

    def test_file_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            self.dedoc_manager.parse_file("afagahcr", {})
