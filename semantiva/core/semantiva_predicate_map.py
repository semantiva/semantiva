from rdflib import Namespace

# Define Semantiva's semantic namespace
SMTV = Namespace("http://semantiva.org/semantiva#")


# Component metadata keys to predicate map
# These are the keys that will be used to extract metadata from the component classes
# and map them to the corresponding RDF predicates in the ontology.
# The keys in this dictionary should match the keys used in the component classes' metadata
PREDICATE_MAP = {
    "class_name": SMTV.className,
    "component_type": SMTV.componentType,
    "docstring": SMTV.docString,
    "input_data_type": SMTV.inputDataType,
    "output_data_type": SMTV.outputDataType,
    "wraps_component_type": SMTV.wrapsComponentType,
    "wraped_component": SMTV.wrapedComponent,
    "wraped_component_docstring": SMTV.processorDocString,
    "injected_context_keys": SMTV.injectedContextKey,
    "input_parameters": SMTV.inputParameter,
    "suppressed_context_keys": SMTV.suppressedKey,
    "collection_element_type": SMTV.collectionElementType,
    "required_context_keys": SMTV.requiredContextKey,
}
