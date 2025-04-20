"""
Test the SemantivaObject class for proper metadata handling and metaclass-based component registration.

This module verifies that:
- Valid components correctly register in the global registry.
- Invalid metadata definitions raise appropriate errors.
- The semantic identifier (semantic_id) is formatted with essential metadata.
"""

import pytest
from semantiva.core.semantiva_object import (
    SemantivaObject,
    get_component_registry,
)


# Dummy base to allow registration in subclasses (avoids direct SemantivaObject inheritance)
class DummyBase(SemantivaObject):
    @classmethod
    def _define_metadata(cls):
        # Return an empty dict so that DummyBase itself doesn't register (no component_type)
        return {}


# Valid component should be automatically registered in the global registry
class ValidComponent(DummyBase):
    @classmethod
    def _define_metadata(cls):
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
