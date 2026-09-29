"""Downloading models in advance for offline library usage."""
from argparse import ArgumentParser

from dedoc_future.env import get_artifacts_path
from dedoc_future.helpers.artifacts.configuration import ARTIFACTS

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--out_dir", "-o", type=str, default=get_artifacts_path(), help="Path to output directory")
    parser.add_argument(
        "--model", "-m", type=str, choices=list(ARTIFACTS.keys()), action="append",
        help="Artifact name to download. If not given, all artifacts will be downloaded"
    )
    args = parser.parse_args()

    artifacts_keys = args.model if args.model else ARTIFACTS.keys()
    for key in artifacts_keys:
        ARTIFACTS[key].download(args.out_dir)
