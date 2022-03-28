import os
from typing import List

from style_test import StyleTest


class TestCodeFormat(StyleTest):

    def get_files(self) -> List[str]:
        files = []
        for code_dir in ["dedoc", "tests"]:
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", code_dir))
            for root, _, filenames in os.walk(path):
                for file in filenames:
                    if file.endswith(".py"):
                        files.append(os.path.join(root, file))
        return files

    def test_style(self) -> None:
        self.flake_test()
