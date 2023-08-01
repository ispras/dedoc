import os

from setuptools import setup


if __name__ == "__main__":
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "VERSION"), "r") as f:
        version = f.read()

    # Dynamically set the __version__ attribute
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "dedoc", "version.py"), "w", encoding="utf-8") as f:
        f.write(f'__version__ = "{version}"\n')
    setup(name="dedoc", version=version)
