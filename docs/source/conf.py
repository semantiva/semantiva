# Configuration file for the Sphinx documentation builder.
import os
import sys
import importlib

sys.path.insert(0, os.path.abspath("../.."))

project = "Semantiva"
copyright = "2025, Rafael Pezzi, Marcos Deros"
author = "Rafael Pezzi, Marcos Deros"
release = "0.5.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

try:
    import myst_parser  # noqa: F401

    extensions.append("myst_parser")
except ModuleNotFoundError:
    pass

try:
    import sphinx_autodoc_typehints  # noqa: F401

    extensions.append("sphinx_autodoc_typehints")
except ModuleNotFoundError:
    pass

if os.environ.get("SPHINX_INTERSPHINX", "0") == "1":
    extensions.append("sphinx.ext.intersphinx")
    intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
else:
    intersphinx_mapping = {}

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
typehints_fully_qualified = True
autodoc_typehints = "none"
autodoc_type_aliases = {
    "T": "typing.Any",
    "S": "typing.Any",
    "E": "typing.Any",
    "X": "typing.Any",
    "Y": "typing.Any",
}
nitpicky = False

templates_path = ["_templates"]
exclude_patterns = []

try:
    importlib.import_module("furo")
    html_theme = "furo"
except ModuleNotFoundError:
    html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["custom.css"]


def skip_docstring(app, what, name, obj, options, lines):
    lines[:] = []


def setup(app):
    app.connect("autodoc-process-docstring", skip_docstring)


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
    ("py:class", "_ContextObserver"),
    ("py:class", "semantiva.core.semantiva_component._SemantivaComponent"),
    ("py:class", "semantiva.pipeline.payload_processors._PayloadProcessor"),
    ("py:class", "semantiva.pipeline.nodes.nodes._PipelineNode"),
    ("py:class", "abc.ABC"),
    ("py:class", "T"),
    ("py:class", "S"),
    ("py:class", "E"),
    ("py:class", "X"),
    ("py:class", "Y"),
    ("py:exc", "PipelineConfigurationError"),
    ("py:data", "typing.Any"),
    ("py:data", "typing.Tuple"),
    ("py:data", "typing.Optional"),
    ("py:data", "typing.Callable"),
    ("py:data", "typing.Union"),
    ("py:data", "T"),
    ("py:data", "S"),
    ("py:data", "E"),
    ("py:data", "X"),
    ("py:data", "Y"),
    ("py:class", "concurrent.futures._base.Future"),
    ("py:data", "concurrent.futures._base.Future"),
    ("py:class", "collections.ChainMap"),
    ("py:class", "semantiva.context_processors.context_observer._ContextObserver"),
    ("py:class", "semantiva.data_processors.data_processors._BaseDataProcessor"),
    ("py:mod", "semantiva.pipeline.graph_builder"),
    ("py:data", "typing.Literal"),
]

nitpick_ignore_regex = [
    ("py:class", r".*\.T"),
    ("py:obj", r".*\.T"),
    ("py:class", r".*\.S"),
    ("py:obj", r".*\.S"),
    ("py:class", r".*\.E"),
    ("py:obj", r".*\.E"),
    ("py:class", r".*\.X"),
    ("py:obj", r".*\.X"),
    ("py:class", r".*\.Y"),
    ("py:obj", r".*\.Y"),
]

suppress_warnings = ["intersphinx"]
