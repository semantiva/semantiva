# Configuration file for the Sphinx documentation builder.
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "Semantiva"
copyright = "2025, Rafael Pezzi, Marcos Deros"
author = "Rafael Pezzi, Marcos Deros"
release = "0.5.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
typehints_fully_qualified = True
autodoc_typehints = "description"
nitpicky = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

intersphinx_disabled_domains = ["python"]


templates_path = ["_templates"]
exclude_patterns = []

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Ignore docstring content to suppress formatting warnings


def skip_docstring(app, what, name, obj, options, lines):
    lines[:] = []


def setup(app):
    app.connect("autodoc-process-docstring", skip_docstring)


# Ignore unresolved references from common typing/classes
nitpick_ignore = [
    ("py:class", "typing.Any"),
    ("py:class", "typing.Tuple"),
    ("py:class", "typing.Optional"),
    ("py:class", "typing.Callable"),
    ("py:class", "typing.Union"),
    ("py:class", "logging.Logger"),
    ("py:class", "logging.Formatter"),
    ("py:class", "collections.deque"),
    ("py:class", "_thread.allocate_lock"),
    ("py:class", "threading.Event"),
    ("py:class", "pathlib.Path"),
    ("py:class", "_BaseDataProcessor"),
    ("py:class", "semantiva.core.semantiva_component._SemantivaComponent"),
    ("py:class", "semantiva.pipeline.payload_processors._PayloadProcessor"),
    ("py:class", "semantiva.pipeline.nodes.nodes._PipelineNode"),
    ("py:class", "abc.ABC"),
    ("py:class", "X"),
    ("py:class", "Y"),
    ("py:exc", "PipelineConfigurationError"),
    ("py:data", "typing.Any"),
    ("py:data", "typing.Tuple"),
    ("py:data", "typing.Optional"),
    ("py:data", "typing.Callable"),
    ("py:data", "typing.Union"),
    ("py:class", "concurrent.futures._base.Future"),
    ("py:data", "concurrent.futures._base.Future"),
]

suppress_warnings = ["intersphinx"]
