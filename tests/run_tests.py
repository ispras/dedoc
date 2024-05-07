import os
import unittest

from custom_test_runner import CustomTextTestRunner

TEST_PREFIX = "test_"


def run_test_group(group_name: str) -> None:
    runner = CustomTextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    test_suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), group_name + "_tests"), pattern=f"{TEST_PREFIX}*.py")
    runner.run(test_suite)


if __name__ == "__main__":
    for group in ("unit", "api"):
        run_test_group(group)
