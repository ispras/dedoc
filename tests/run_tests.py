import os
import unittest

from custom_test_runner import CustomTextTestRunner

TEST_PREFIX = "test_"


def run_test_group(group_name: str) -> None:
    runner = CustomTextTestRunner(verbosity=2)
    loader = unittest.TestLoader()
    test_suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{group_name}_tests"), pattern=f"{TEST_PREFIX}*.py")
    result = runner.run(test_suite)
    if len(result.errors) > 0 or len(result.failures) > 0:
        exit(1)


if __name__ == "__main__":
    for group in ("unit", "api"):
        run_test_group(group)
