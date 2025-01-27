# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "Semantiva"
copyright = "2025, Rafael Pezzi, Marcos Deros"
author = "Rafael Pezzi, Marcos Deros"
release = "0.1.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Supports Google-style and NumPy-style docstrings
    "sphinx_autodoc_typehints",  # Adds type hints to your documentation
    "sphinx.ext.autosummary",  # Generates autodoc summaries
]

autodoc_typehints = "description"
templates_path = ["_templates"]
exclude_patterns = []

# Add the _static directory to the static path
html_static_path = ["_static"]

# Include the custom CSS file
html_css_files = [
    "custom.css",
]
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
