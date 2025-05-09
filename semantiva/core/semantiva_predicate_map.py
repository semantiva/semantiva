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
    "input_parameters": SMTV.inputParameters,
    "input_data_type": SMTV.inputDataType,
    "output_data_type": SMTV.outputDataType,
    "wraps_component_type": SMTV.wrapsComponentType,
    "wraped_component": SMTV.wrapedComponent,
    "wraped_component_docstring": SMTV.wrapedComponentDocString,
    "injected_context_keys": SMTV.injectedContextKeys,
    "suppressed_context_keys": SMTV.suppressedContextKeys,
    "required_context_keys": SMTV.requiredContextKeys,
    "collection_element_type": SMTV.collectionElementType,
}
