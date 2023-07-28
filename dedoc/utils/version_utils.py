import os

import dedoc


def get_dedoc_version() -> str:
    if dedoc.__version__ != "":
        return dedoc.__version__

    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", "VERSION"), "r") as f:
        version = f.read()

    # Dynamically set the __version__ attribute
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "version.py"), "w", encoding="utf-8") as f:
        f.write(f'__version__ = "{version}"\n')

    return version


if __name__ == "__main__":
    get_dedoc_version()
