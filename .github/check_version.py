import argparse
import os
import re
import sys
from typing import Pattern


def is_correct_version(version: str, old_version: str, regexp: Pattern) -> bool:
    match = regexp.match(version)

    if match is None:
        return False

    return old_version < version


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", help="Git branch to check its version", enum=["develop", "master", "TLDR-350_pypi_pipeline_fix"])
    parser.add_argument("--new_version", help="Version on this branch", type=str)
    parser.add_argument("--old_version", help="Previous version on this branch", type=str)
    args = parser.parse_args()

    master_version_pattern = re.compile(r"^\d+\.\d+(\.\d+)?$")
    develop_version_pattern = re.compile(r"^\d+\.\d+\.\d+rc\d+$")

    correct = False
    if args.branch == "develop" or args.branch == "TLDR-350_pypi_pipeline_fix":
        correct = is_correct_version(args.new_version, args.old_version, develop_version_pattern)

    if args.branch == "master":
        correct = is_correct_version(args.new_version, args.old_version, master_version_pattern)

    if correct:
        sys.exit(0)
    else:
        sys.exit(1)
