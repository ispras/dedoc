import os
from pathlib import Path

_DEFAULT_ARTIFACTS_PATH = str((Path("~") / ".cache" / "dedoc").expanduser())


def get_artifacts_path(default: str = _DEFAULT_ARTIFACTS_PATH) -> str:
    return os.getenv("DEDOC_ARTIFACTS_PATH", default)
