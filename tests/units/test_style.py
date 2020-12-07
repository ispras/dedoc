import unittest

import pycodestyle
import os


class TestCodeFormat(unittest.TestCase):

    @staticmethod
    def get_files():
        files = []
        for code_dir in ["dedoc", "tests"]:
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", code_dir))
            for root, _, filenames in os.walk(path):
                for file in filenames:
                    if file.endswith(".py"):
                        files.append(os.path.join(root, file))
        return files

    def test_pep8_conformance(self):
        """Test that we conform to PEP8."""

        files = self.get_files()
        ignore = [
            "E501",  # skip line length check because  79 is not enough
            "W504"  # we choose this from 503 and 504
        ]
        pep8style = pycodestyle.StyleGuide(quiet=True, ignore=ignore)
        file_check = pep8style.check_files(files)
        if file_check.total_errors > 0:
            print("GET {} ERRORS".format(file_check.total_errors))
            pep8style = pycodestyle.StyleGuide(quiet=False, ignore=ignore)
            pep8style.check_files(files)

        self.assertEqual(0, file_check.total_errors, "some file contains errors. To skip line use # noqa")
