# noqa
import os
import re
import unittest
import warnings
from typing import List, Tuple
import pycodestyle
from flake8.api import legacy as flake8


class TestCodeFormat(unittest.TestCase):

    @staticmethod
    def get_files() -> List[str]:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dedoc"))
        files = []
        for root, _, filenames in os.walk(path):
            for file in filenames:
                if not file.endswith(".py"):
                    continue
                with open(os.path.join(root, file), "r") as f:
                    first_line = f.readline()
                # ignore files with "noqa" in the beginning
                if "# noqa" not in first_line:
                    files.append(os.path.join(root, file))
        return files

    def test_pep8_conformance(self) -> None:
        """Test that we conform to PEP8."""

        files = self.get_files()
        ignore = [
            "E501",  # skip line length check because  79 is not enough
            "W504"  # we choose this from 503 and 504
        ]
        pep8style = pycodestyle.StyleGuide(quiet=True, ignore=ignore)
        file_check = pep8style.check_files(files)
        if file_check.total_errors > 0:
            print("GET {} ERRORS".format(file_check.total_errors))  # noqa
            pep8style = pycodestyle.StyleGuide(quiet=False, ignore=ignore)
            pep8style.check_files(files)

        self.assertEqual(0, file_check.total_errors, "some file contains errors. To skip line use # noqa")

    def test_forgotten_print(self) -> None:
        """tests that we did not forget some prints in code,
         It's ok use print in scripts, if you want to use print in other places mark them with   # noqa
         """
        files = self.get_files()
        print_regexp = re.compile(r"\s*print\(")
        prints_cnt = 0
        for file_path in files:
            with open(file_path) as file:
                for line_id, line in enumerate(file):
                    if print_regexp.match(line) and "scripts/" not in file_path:
                        if "# noqa" not in line:
                            warnings.warn("seems you forgot print in \n{}:{}".format(file_path, line_id))
                            prints_cnt += 1
        self.assertEqual(0, prints_cnt)

    def test_flake(self) -> None:
        """Test that we conform to flake."""
        style_guide = flake8.get_style_guide(ignore=["E501", "W504", "ANN101", "TYP101"])
        files = self.get_files()
        errors = style_guide.check_files(files)
        self.assertEqual(0, errors.total_errors)

    def test_forgotten_removes(self) -> None:
        broken_files = 0
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
        for path in self.get_files():
            if "test_style.py" in path:
                continue
            with open(path) as file:
                for line_id, line in enumerate(file):
                    if "#TODOREMOVE" in line.upper().replace(" ", "") and "# noqa" in line.lower(): # noqa
                        print("{}:{}".format(path[len(project_root):], line_id + 1))   # noqa
                        broken_files += 1
        self.assertEqual(0, broken_files)

    def test_imports(self) -> None:
        too_many_blocks = []
        import_not_from_root = []
        for file in self.get_files():
            self.__check_imports(file, import_not_from_root, too_many_blocks)
        if len(too_many_blocks) > 0:
            res = "\n\n"
            for line in too_many_blocks:
                res += line + ":1\n"
            warnings.warn(res)
        self.assertEqual(0, len(too_many_blocks))
        if len(import_not_from_root) > 0:
            res = "\n\n"
            for line_id, line in import_not_from_root:
                res += line + ":{}\n".format(line_id + 1)
            warnings.warn(res)
        self.assertEqual(0, len(import_not_from_root))

    def __check_imports(self, file: str, import_not_from_root: list, too_many_blocks: list) -> None:
        blocks = self._get_import_blocks(file)
        if len(blocks) > 3:
            too_many_blocks.append(file)
        prefix_for_local_imports = ("dedoc", "tests", "config")
        if len(blocks) == 3:
            for line_id, line in blocks[2]:
                local_imports_correct = line.split()[1].startswith(prefix_for_local_imports)
                if not local_imports_correct:
                    import_not_from_root.append((line_id, file))

    def _get_import_blocks(self, file: str) -> List[List[Tuple[int, str]]]:
        blocks = []
        block = []
        prev_line = ""
        with open(file) as in_file:
            for line_id, line in enumerate(in_file):
                if prev_line.strip().endswith("\\"):
                    prev_line = line
                    continue
                elif line.strip().startswith("#"):
                    continue
                elif line.strip() == "":
                    if len(block) > 0:
                        blocks.append(block)
                    block = []
                else:
                    block.append((line_id, line))
                prev_line = line
        return [block for block in blocks if all(line.startswith(("import", "from")) for _, line in block)]
