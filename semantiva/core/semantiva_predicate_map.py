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

from rdflib import Namespace

# Define Semantiva's semantic namespace
SMTV = Namespace("http://semantiva.org/semantiva#")


# Experimental component metadata keys to predicate map
# These are the keys that will be used to extract metadata from the component classes
# and map them to the corresponding RDF predicates in the ontology.
# The keys in this dictionary should match the keys used in the component classes' metadata

# This is experimental and may change in future versions of Semantiva.

EXPERIMENTAL_PREDICATE_MAP = {
    "class_name": SMTV.className,
    "component_type": SMTV.componentType,
    "docstring": SMTV.docString,
    "parameters": SMTV.parameters,
    "input_data_type": SMTV.inputDataType,
    "output_data_type": SMTV.outputDataType,
    "wraps_component_type": SMTV.wrapsComponentType,
    "wrapped_component": SMTV.wrappedComponent,
    "wrapped_component_docstring": SMTV.wrappedComponentDocString,
    "injected_context_keys": SMTV.injectedContextKeys,
    "suppressed_context_keys": SMTV.suppressedContextKeys,
    "required_context_keys": SMTV.requiredContextKeys,
    "collection_element_type": SMTV.collectionElementType,
}
