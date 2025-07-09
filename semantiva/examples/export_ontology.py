# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# semantiva/examples/export_ontology.py
"""
Export the Semantiva component taxonomy and metadata to RDF/Turtle using live framework metadata.
Sample usage:
    python semantiva/examples/export_ontology.py -o semantiva_ontology.ttl -p semantiva,semantiva_imaging

This is an experimental tool, not part of the public API.
"""
import sys
import pkgutil
import inspect
import importlib
from typing import List
from rdflib import Graph, RDF, RDFS, OWL, Literal
from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.core.semantiva_predicate_map import SMTV, EXPERIMENTAL_PREDICATE_MAP


def _discover_and_import(package_name: str) -> None:
    """
    Discover and import all modules in the specified package.
    """
    pkg = importlib.import_module(package_name)
    prefix = pkg.__name__ + "."
    if hasattr(pkg, "__path__"):
        for _, modname, _ in pkgutil.walk_packages(pkg.__path__, prefix):
            try:
                importlib.import_module(modname)
            except Exception:
                pass


def _collect_components(packages: List[str]) -> List[type[_SemantivaComponent]]:
    """
    Collect all _SemantivaComponent subclasses from the specified packages.
    """
    duplicates = []
    for pkg in packages:
        _discover_and_import(pkg)
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", "")
        if not path:
            continue
        if any(module.__name__.startswith(root + ".") for root in packages):
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(cls, _SemantivaComponent)
                    and cls is not _SemantivaComponent
                ):
                    duplicates.append(cls)
    # Deduplicate preserving order
    seen = set()
    components = []
    for cls in duplicates:
        if cls not in seen:
            seen.add(cls)
            components.append(cls)
    return components


def _export_framework_ontology(output_path: str, packages: list[str]) -> None:
    """
    Export the Semantiva component ontology to a Turtle file with metadata.
    """
    g = Graph()
    g.bind("smtv", SMTV)

    g.add((SMTV.hasCategory, RDF.type, OWL.ObjectProperty))
    g.add((SMTV.hasCategory, RDFS.label, Literal("has category")))

    for cls in _collect_components(packages):
        if not hasattr(cls, "get_metadata"):
            continue
        metadata = cls.get_metadata()
        class_name = metadata.get("class_name", cls.__name__)
        uri = SMTV[class_name]

        # Declare as OWL class
        g.add((uri, RDF.type, OWL.Class))
        g.add((uri, RDFS.label, Literal(class_name)))

        # Subclass relationship for first base class
        base = cls.__bases__[0]
        if base is not object and hasattr(base, "__name__"):
            g.add((uri, RDFS.subClassOf, SMTV[base.__name__]))

        # Emit metadata triples
        for key in metadata.keys():
            if key not in EXPERIMENTAL_PREDICATE_MAP and key != "class_name":
                print(f"Warning: No predicate for '{key}' in {class_name}")
        for key, predicate in EXPERIMENTAL_PREDICATE_MAP.items():
            value = metadata.get(key)
            if not value:
                continue
            if isinstance(value, (list, tuple)):
                for item in value:
                    g.add((uri, predicate, Literal(str(item))))
            else:
                g.add((uri, predicate, Literal(str(value))))

                # Group component under its category by adding an additional rdf:type
        category = metadata.get("component_type")
        if category:
            smtv_category = (
                SMTV[category] if category != class_name else SMTV[base.__name__]
            )
            g.add((uri, RDF.type, smtv_category))

    # Serialize to Turtle
    g.serialize(destination=output_path, format="turtle")
    print(f"Exported {len(g)} triples to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Export Semantiva component ontology to TTL with category grouping [experimental]"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="semantiva_components.ttl",
        help="Destination TTL file",
    )
    parser.add_argument(
        "--packages", "-p", default="semantiva", help="Comma-separated list of packages"
    )
    args = parser.parse_args()
    package_list = args.packages.split(",") if args.packages else []
    _export_framework_ontology(args.output, package_list)
