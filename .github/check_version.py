import argparse
import re
from typing import Pattern


def is_correct_version(version: str, tag: str, old_version: str, regexp: Pattern) -> bool:
    match = regexp.match(version)

    if match is None:
        print("New version doesn't match the pattern")  # noqa
        return False

    if not (tag.startswith("v") and tag[1:] == version):
        print("Tag value should be equal to version with `v` in the beginning")  # noqa
        return False

    return old_version < version


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", help="Git branch to check its version", choices=["develop", "master"])
    parser.add_argument("--tag", help="Tag of the release", type=str)
    parser.add_argument("--pre_release", help="Tag of the release", choices=["true", "false"])
    parser.add_argument("--new_version", help="New release version", type=str)
    parser.add_argument("--old_version", help="Previous release version", type=str)
    args = parser.parse_args()

    print(f"Old version: {args.old_version}, new version: {args.new_version}, "
          f"branch: {args.branch}, tag: {args.tag}, pre_release: {args.pre_release}")  # noqa

    master_version_pattern = re.compile(r"^\d+\.\d+(\.\d+)?$")
    develop_version_pattern = re.compile(r"^\d+\.\d+\.\d+rc\d+$")

    correct = False
    if args.branch == "develop":
        correct = is_correct_version(args.new_version, args.tag, args.old_version, develop_version_pattern)

        if correct and master_version_pattern.match(args.old_version) and args.new_version.split("rc")[0] <= args.old_version:
            correct = False
            print("New version should add 'rc' to the bigger version than the old one")  # noqa
        elif correct and int(args.new_version.split("rc")[1]) == 0:
            correct = False
            print("Numeration for 'rc' should start from 1")  # noqa

        if args.pre_release == "false":
            correct = False
            print("Only pre-releases allowed on develop")  # noqa

    if args.branch == "master":
        correct = is_correct_version(args.new_version, args.tag, args.old_version, master_version_pattern)

        if args.pre_release == "true":
            correct = False
            print("Pre-releases are not allowed on master")  # noqa

    assert correct
    print("Version is correct")  # noqa
