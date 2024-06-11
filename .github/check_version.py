import argparse
import re
from typing import Pattern

from pkg_resources import parse_version


def is_correct_version(version: str, tag: str, old_version: str, regexp: Pattern) -> None:
    match = regexp.match(version)

    assert match is not None, "New version doesn't match the pattern"
    assert tag.startswith("v") and tag[1:] == version, "Tag value should be equal to version with `v` in the beginning"
    assert parse_version(old_version) < parse_version(version), "New version should be greater than old version"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", help="Git branch to check its version", choices=["develop", "master"])
    parser.add_argument("--tag", help="Tag of the release", type=str)
    parser.add_argument("--pre_release", help="Tag of the release", choices=["true", "false"])
    parser.add_argument("--new_version", help="New release version", type=str)
    parser.add_argument("--old_version", help="Previous release version", type=str)
    args = parser.parse_args()

    print(f"Old version: {args.old_version}, new version: {args.new_version}, "
          f"branch: {args.branch}, tag: {args.tag}, pre_release: {args.pre_release}")

    master_version_pattern = re.compile(r"^\d+\.\d+(\.\d+)?$")
    develop_version_pattern = re.compile(r"^\d+\.\d+\.\d+rc\d+$")

    correct = False
    if args.branch == "develop":
        is_correct_version(args.new_version, args.tag, args.old_version, develop_version_pattern)

        if master_version_pattern.match(args.old_version) and args.new_version.split("rc")[0] <= args.old_version:
            assert False, "New version should add 'rc' to the bigger version than the old one"
        elif int(args.new_version.split("rc")[1]) == 0:
            assert False, "Numeration for 'rc' should start from 1"

        assert args.pre_release != "false", "Only pre-releases allowed on develop"

    if args.branch == "master":
        is_correct_version(args.new_version, args.tag, args.old_version, master_version_pattern)
        assert args.pre_release != "true", "Pre-releases are not allowed on master"

    print("Version is correct")
