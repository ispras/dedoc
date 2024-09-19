import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "labeling")))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))


# -- Project information -----------------------------------------------------

project = "dedoc"
_copyright_str = f"-{datetime.now().year}" if datetime.now().year > 2023 else ""
copyright = f"2023{_copyright_str}, Dedoc team"  # noqa
author = "Dedoc team"
release = "1"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
    "sphinx_copybutton",
    "sphinx_togglebutton",
    "linuxdoc.rstFlatTable"
]
exclude_patterns = []
highlight_language = "python3"

# -- Options for the nitpicky mode -------------------------------------------

nitpicky = True
nitpick_ignore = [
    ("py:class", "abc.ABC"),
    ("py:class", "pydantic.main.BaseModel"),
    ("py:class", "scipy.stats._multivariate.dirichlet_multinomial_gen.cov"),
    ("py:class", "pandas.core.series.Series"),
    ("py:class", "numpy.ndarray"),
    ("py:class", "pandas.core.frame.DataFrame"),
    ("py:class", "dedoc.structure_extractors.feature_extractors.toc_feature_extractor.TocItem"),
    ("py:class", "logging.Logger"),
    ("py:class", "train_dataset.data_structures.line_with_label.LineWithLabel"),
    ("py:class", "xgboost.sklearn.XGBClassifier"),
    ("py:class", "collections.Counter"),
    ("py:obj", "typing.Pattern")
]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["style.css"]
html_favicon = "_static/favicon.ico"
html_title = "dedoc documentation"
