from setuptools import setup

from dedoc.utils.version_utils import get_dedoc_version

if __name__ == "__main__":
    setup(name="dedoc", version=get_dedoc_version())
