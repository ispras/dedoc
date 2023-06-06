import argparse
import re
from typing import Pattern


def is_correct_version(version: str, old_version: str, regexp: Pattern) -> bool:
    match = regexp.match(version)

    if match is None:
        print("New version doesn't match the pattern")  # noqa
        return False

    return old_version < version


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", help="Git branch to check its version", choices=["develop", "master", "TLDR-350_pypi_pipeline_fix"])
    parser.add_argument("--new_version", help="Version on this branch", type=str)
    parser.add_argument("--old_version", help="Previous version on this branch", type=str)
    args = parser.parse_args()

    print(f"Old version: {args.old_version}, new version: {args.new_version}")  # noqa

    master_version_pattern = re.compile(r"^\d+\.\d+(\.\d+)?$")
    develop_version_pattern = re.compile(r"^\d+\.\d+\.\d+rc\d+$")

    correct = False
    if args.branch == "develop" or args.branch == "TLDR-350_pypi_pipeline_fix":
        correct = is_correct_version(args.new_version, args.old_version, develop_version_pattern)

        old_match_master = master_version_pattern.match(args.old_version)
        # we should add 'rc' to the bigger version than the old one
        if correct and old_match_master and args.new_version.split("rc")[0] <= args.old_version:
            correct = False
            print("New version should add 'rc' to the bigger version than the old one")  # noqa
        elif correct and old_match_master and int(args.new_version.split("rc")[1]) == 0:
            correct = False
            print("Numeration for 'rc' should start from 1")  # noqa

    if args.branch == "master":
        correct = is_correct_version(args.new_version, args.old_version, master_version_pattern)

    assert correct
    print("Version is correct")  # noqa
