# semantiva/tools/export_ontology.py
"""
Export the Semantiva component taxonomy and metadata to RDF/Turtle using live framework metadata.
Sample usage:
    python semantiva/tools/export_ontology.py -o semantiva_ontology.ttl -p semantiva
    python semantiva/tools/export_ontology.py -o semantiva_ontology.ttl -p semantiva,semantiva_imaging
"""
import sys
import pkgutil
import inspect
import importlib
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal
from semantiva.core.semantiva_object import SemantivaObject, get_component_registry

# Define our semantic namespace    get_component_registry,

SMTV = Namespace("http://semantiva.org/semantiva#")

# Component metadata keys to predicate map
# These are the keys that will be used to extract metadata from the component classes
# and map them to the corresponding RDF predicates in the ontology.
# The keys in this dictionary should match the keys used in the component classes' metadata
PREDICATE_MAP = {
    "component_type": SMTV.componentType,
    "docstring": SMTV.docString,
    "input_parameters": SMTV.inputParameter,
    "created_keys": SMTV.createdKey,
    "suppressed_keys": SMTV.suppressedKey,
    "input_data_type": SMTV.inputDataType,
    "output_data_type": SMTV.outputDataType,
    "injected_context_keys": SMTV.injectedContextKey,
    "payload_source": SMTV.payloadSource,
    "payload_sink": SMTV.payloadSink,
    "processor": SMTV.processor,
    "processor_docstring": SMTV.processorDocString,
    "context_processor": SMTV.contextProcessor,
}


def discover_and_import(package_name: str):
    """
    Discover and import all modules in the specified package.
    """
    pkg = importlib.import_module(package_name)
    prefix = pkg.__name__ + "."
    for finder, modname, is_pkg in pkgutil.walk_packages(pkg.__path__, prefix):
        try:
            importlib.import_module(modname)
        except Exception:
            # skip modules with import errors
            continue


def collect_components(packages):
    """
    Collect all SemantivaObject subclasses from the specified packages.
    """
    components = []
    for pkg in packages:
        discover_and_import(pkg)
    # Now every module under those roots is loaded
    for pkg in packages:
        pkg_mod = importlib.import_module(pkg)
        for module in list(sys.modules.values()):
            if not getattr(module, "__file__", ""):
                continue
            # Only consider modules in our roots
            if any(module.__name__.startswith(root + ".") for root in packages):
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, SemantivaObject) and obj is not SemantivaObject:
                        components.append(obj)
    return list({c: None for c in components}.keys())  # dedupe


def export_framework_ontology(output_path: str, packages: list[str]) -> None:
    """
    Export the Semantiva component ontology to a Turtle file with metadata.
    """
    # Create a new RDF graph
    g = Graph()
    g.bind("smtv", SMTV)  # Bind the semantic namespace

    # Iterate through all packages
    for cls in collect_components(packages):
        # Get class-level semantic metadata
        package = cls.__module__.split(".")[0]
        if hasattr(cls, "get_metadata"):
            metadata = cls.get_metadata()
            uri = SMTV[cls.__name__]

            # Declare the class as OWL class
            g.add((uri, RDF.type, OWL.Class))
            # g.add((uri, RDFS.label, Literal(package)))
            g.add((uri, RDFS.label, Literal(cls.__name__)))

            # if category != cls.__name__:
            g.add((uri, RDFS.subClassOf, SMTV[cls.__bases__[0].__name__]))

            # Add semantic metadata triples
            for key, predicate in PREDICATE_MAP.items():
                value = metadata.get(key)
                if not value:
                    continue
                # Normalize list or single
                if isinstance(value, (list, tuple)):
                    for item in value:
                        g.add((uri, predicate, Literal(str(item))))
                else:
                    g.add((uri, predicate, Literal(str(value))))

    # Serialize to Turtle
    g.serialize(destination=output_path, format="turtle")
    print(f"Exported {len(g)} triples to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Export Semantiva component ontology to TTL with metadata"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="semantiva_components.ttl",
        help="Destination TTL file",
    )

    parser.add_argument(
        "--packages",
        "-p",
        default="semantiva",
        help="Comma-separated list of packages to scan for components",
    )
    args = parser.parse_args()
    package_list = args.packages.split(",") if args.packages else []
    export_framework_ontology(args.output, package_list)
