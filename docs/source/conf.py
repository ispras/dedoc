from datetime import datetime


# -- Path setup --------------------------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))


# -- Project information -----------------------------------------------------

project = 'dedoc'
_copyright_str = f"-{datetime.now().year}" if datetime.now().year > 2023 else ""
copyright = f'2023{_copyright_str}, Dedoc team'
author = 'Dedoc team'
release = '1'


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    'sphinx_rtd_theme'
]
exclude_patterns = []
highlight_language = "python3"

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['style.css']
html_favicon = '_static/favicon.ico'
html_title = 'dedoc documentation'
