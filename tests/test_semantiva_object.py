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

"""
Test the _SemantivaComponent class for proper metadata handling and metaclass-based component registration.

This module verifies that:
- Valid components correctly register in the global registry.
- Invalid metadata definitions raise appropriate errors.
- The semantic identifier (semantic_id) is formatted with essential metadata.
"""

import pytest
from pprint import pprint
import inspect
from typing import Dict, Any
from semantiva.core.semantiva_component import (
    _SemantivaComponent,
    get_component_registry,
)
from semantiva.examples.export_ontology import _collect_components


# Dummy base to allow registration in subclasses (avoids direct _SemantivaComponent inheritance)
class DummyBase(_SemantivaComponent):
    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        # Return an empty dict so that DummyBase itself doesn't register (no component_type)
        return {}


# Valid component should be automatically registered in the global registry
class ValidComponent(DummyBase):
    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        return {"component_type": "Test", "some_key": "value"}


# Invalid component returns non-dict metadata and should raise TypeError when get_metadata is called
class InvalidComponent(DummyBase):
    @classmethod
    def _define_metadata(cls):
        return "invalid metadata"


def test_registration_of_valid_component():
    """
    Test that ValidComponent is registered in the global registry
    under its declared component_type.
    """
    # Trigger registration by referencing ValidComponent metadata
    _ = ValidComponent.get_metadata()

    registry = get_component_registry()
    assert "Test" in registry, "Expected 'Test' to be a key in the registry."
    # The registration should include ValidComponent
    assert ValidComponent in registry["Test"], "ValidComponent should be registered."


def test_invalid_component_get_metadata_raises():
    """
    Test that calling get_metadata on an invalid component
    (one that returns non-dict metadata) raises a TypeError.
    """
    with pytest.raises(TypeError):
        _ = InvalidComponent.get_metadata()


def test_semantic_id_format():
    """
    Test that semantic_id returns a formatted multi-line string containing
    key pieces of metadata.
    """
    # Ensure ValidComponent is registered and has valid metadata
    metadata = ValidComponent.get_metadata()
    semantic_id = ValidComponent.semantic_id()

    expected_header = "========  SEMANTIC ID  ========"
    assert expected_header in semantic_id, "Semantic ID should include header line."

    # Check that the class name is properly displayed
    assert (
        f"Class Name: {ValidComponent.__name__}" in semantic_id
    ), "Semantic ID should include the class name."

    # Optionally, verify that other metadata keys appear in the output
    for key in metadata:
        if key not in ("docstring", "processor_docstring", "class_name"):
            assert (
                str(metadata[key]) in semantic_id
            ), f"Metadata key '{key}' should appear in semantic_id."


@pytest.mark.parametrize(
    "component_cls,expected_metadata",
    [
        (
            ValidComponent,
            {
                "class_name": "ValidComponent",
                "docstring": inspect.getdoc(ValidComponent)
                or "No documentation available.",
                "component_type": "Test",
                "some_key": "value",
            },
        ),
        (
            InvalidComponent,
            None,  # This one is expected to raise TypeError, tested separately
        ),
        (
            DummyBase,
            {
                "class_name": "DummyBase",
                "docstring": inspect.getdoc(DummyBase) or "No documentation available.",
            },
        ),
    ],
)
def test_get_metadata_values(component_cls, expected_metadata):
    """
    For every component that defines _define_metadata, test that get_metadata returns the correct values.
    """
    if expected_metadata is None:
        with pytest.raises(TypeError):
            component_cls.get_metadata()
    else:
        metadata = component_cls.get_metadata()
        for key, value in expected_metadata.items():
            assert (
                metadata[key] == value
            ), f"Metadata key '{key}' mismatch for {component_cls.__name__}"


def test_semantic_id_metadata_consistency():
    """
    For every registered component, ensure that all get_metadata keys (except docstring, processor_docstring, class_name)
    appear in the semantic_id output.
    """
    _collect_components(["semantiva"])
    registry = get_component_registry()
    for category, classes in registry.items():
        for cls in classes:
            metadata = cls.get_metadata()
            semantic_id = cls.semantic_id()
            assert (
                "component_type" in metadata
            ), f"Component type not found in metadata for {cls.__name__}"
            print(f"Testing {cls.__name__} for metadata consistency in metadata:")
            pprint(metadata)
            print(f"     semantic_id: {semantic_id}")
            print("--------------------------")
            for key, value in metadata.items():
                if key not in (
                    "docstring",
                    "wrapped_component_docstring",
                    # "class_name",
                    "parameters",
                ):
                    print(f"     Checking key '{key}', {value} in semantic_id")
                    if isinstance(value, list):
                        for item in value:
                            print(f"         Checking item '{item}' in semantic_id")
                            assert (
                                str(item) in semantic_id
                            ), f"List item '{item}' for key '{key}' not found in semantic_id for {cls.__name__}"
                    else:
                        assert (
                            str(value) in semantic_id
                        ), f"Value for key '{key}' ({value}) not found in semantic_id for {cls.__name__}"
