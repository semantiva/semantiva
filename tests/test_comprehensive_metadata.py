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
Comprehensive Component Metadata Testing

This module provides systematic testing of ALL Semantiva components' metadata
to ensure consistency, completeness, and compliance with framework contracts.

Design Principles:
- Test ALL components that inherit from _SemantivaComponent
- Ensure consistent metadata structure across component types
- Validate framework contracts (e.g., component_type presence)
- Avoid duplication with functionality tests in other modules
"""

import pytest
from pprint import pprint
from typing import Dict, Any, Type, Set
from semantiva.core.semantiva_component import (
    _SemantivaComponent,
    get_component_registry,
)
from semantiva.examples.export_ontology import _collect_components


def get_all_semantiva_components() -> Set[Type[_SemantivaComponent]]:
    """
    Discover all Semantiva components in the framework.

    Returns:
        Set of all _SemantivaComponent subclasses found in the semantiva package
    """
    return set(_collect_components(["semantiva"]))


def get_concrete_test_components() -> Set[Type[_SemantivaComponent]]:
    """
    Get concrete test components from test_utils for detailed validation.

    Returns:
        Set of concrete test components that can be instantiated
    """
    from semantiva.examples.test_utils import (
        FloatDataSource,
        FloatPayloadSource,
        FloatDataSink,
        FloatPayloadSink,
        FloatMultiplyOperation,
        FloatBasicProbe,
        FloatCollectionSumOperation,
    )

    concrete_components: Set[Type[_SemantivaComponent]] = {
        FloatDataSource,
        FloatPayloadSource,
        FloatDataSink,
        FloatPayloadSink,
        FloatMultiplyOperation,
        FloatBasicProbe,
        FloatCollectionSumOperation,
    }
    return concrete_components


class TestFrameworkMetadataContracts:
    """Test framework-level metadata contracts for ALL components."""

    def test_all_components_have_metadata(self):
        """Ensure ALL Semantiva components implement _define_metadata."""
        components = get_all_semantiva_components()

        for component_cls in components:
            # Skip abstract base classes that shouldn't be instantiated
            if (
                component_cls.__name__.startswith("_")
                and component_cls.__name__ != "_SemantivaComponent"
            ):
                continue

            try:
                metadata = component_cls._define_metadata()
                assert isinstance(
                    metadata, dict
                ), f"{component_cls.__name__}._define_metadata() must return a dict"
            except Exception as e:
                pytest.fail(f"{component_cls.__name__}._define_metadata() failed: {e}")

    def test_all_components_have_get_metadata(self):
        """Ensure ALL components provide valid get_metadata() output."""
        components = get_all_semantiva_components()

        for component_cls in components:
            if (
                component_cls.__name__.startswith("_")
                and component_cls.__name__ != "_SemantivaComponent"
            ):
                continue

            try:
                metadata = component_cls.get_metadata()
                assert isinstance(
                    metadata, dict
                ), f"{component_cls.__name__}.get_metadata() must return a dict"
                assert (
                    "class_name" in metadata
                ), f"{component_cls.__name__} metadata missing 'class_name'"
                assert (
                    "docstring" in metadata
                ), f"{component_cls.__name__} metadata missing 'docstring'"
            except Exception as e:
                pytest.fail(f"{component_cls.__name__}.get_metadata() failed: {e}")

    def test_all_components_have_semantic_id(self):
        """Ensure ALL components provide valid semantic_id() output."""
        components = get_all_semantiva_components()

        for component_cls in components:
            if (
                component_cls.__name__.startswith("_")
                and component_cls.__name__ != "_SemantivaComponent"
            ):
                continue

            try:
                semantic_id = component_cls.semantic_id()
                assert isinstance(
                    semantic_id, str
                ), f"{component_cls.__name__}.semantic_id() must return a string"
                assert (
                    len(semantic_id) > 0
                ), f"{component_cls.__name__}.semantic_id() cannot be empty"
                assert (
                    "SEMANTIC ID" in semantic_id
                ), f"{component_cls.__name__}.semantic_id() should contain header"
            except Exception as e:
                pytest.fail(f"{component_cls.__name__}.semantic_id() failed: {e}")


class TestComponentTypeSpecificMetadata:
    """Test component type-specific metadata requirements."""

    def test_registered_components_have_component_type(self):
        """Ensure components registered in the registry have component_type."""
        registry = get_component_registry()

        for component_type, components in registry.items():
            for component_cls in components:
                metadata = component_cls.get_metadata()
                assert (
                    "component_type" in metadata
                ), f"{component_cls.__name__} missing 'component_type'"
                # The component_type in metadata should match registry key
                assert (
                    metadata["component_type"] == component_type
                ), f"{component_cls.__name__} component_type mismatch"

    def test_data_io_components_have_data_types(self):
        """Ensure DataSource, DataSink, PayloadSource, PayloadSink have data type metadata."""
        registry = get_component_registry()

        # Only concrete data I/O components should have data type information
        # Node classes are wrappers and may have different metadata structure
        data_io_types = ["DataSource", "DataSink", "PayloadSource", "PayloadSink"]

        for component_type in data_io_types:
            if component_type in registry:
                for component_cls in registry[component_type]:
                    # Skip abstract base classes
                    if component_cls.__name__.startswith("_") and not hasattr(
                        component_cls, "output_data_type"
                    ):
                        continue

                    metadata = component_cls.get_metadata()

                    # Sources should have output_data_type
                    if "Source" in component_type:
                        assert (
                            "output_data_type" in metadata
                        ), f"{component_cls.__name__} missing 'output_data_type'"

                    # Sinks should have input_data_type
                    if "Sink" in component_type:
                        assert (
                            "input_data_type" in metadata
                        ), f"{component_cls.__name__} missing 'input_data_type'"

    def test_data_processors_have_data_types(self):
        """Ensure concrete DataOperation and DataProbe components have input/output data type metadata."""
        registry = get_component_registry()

        # Only concrete processor components should have data type information
        # Abstract base classes and node wrappers may have different metadata structure
        processor_types = ["DataOperation", "DataProbe"]

        for component_type in processor_types:
            if component_type in registry:
                for component_cls in registry[component_type]:
                    # Skip abstract base classes that don't have concrete data types
                    if component_cls.__name__ in ["DataOperation", "DataProbe"]:
                        continue

                    metadata = component_cls.get_metadata()

                    # All concrete processors should have input data type
                    assert (
                        "input_data_type" in metadata
                    ), f"{component_cls.__name__} missing 'input_data_type'"

                    # Operations should have output data type
                    if "Operation" in component_type:
                        assert (
                            "output_data_type" in metadata
                        ), f"{component_cls.__name__} missing 'output_data_type'"

    def test_node_wrapper_classes_have_consistent_metadata(self):
        """Ensure Node wrapper classes have consistent metadata structure."""
        registry = get_component_registry()

        # Node classes are wrappers around processors
        node_types = [
            "DataSourceNode",
            "DataSinkNode",
            "PayloadSourceNode",
            "PayloadSinkNode",
            "DataOperationNode",
            "ProbeNode",
        ]

        for component_type in node_types:
            if component_type in registry:
                for component_cls in registry[component_type]:
                    metadata = component_cls.get_metadata()

                    # All nodes should have basic metadata
                    assert (
                        "component_type" in metadata
                    ), f"{component_cls.__name__} missing 'component_type'"
                    assert (
                        "class_name" in metadata
                    ), f"{component_cls.__name__} missing 'class_name'"
                    assert (
                        "docstring" in metadata
                    ), f"{component_cls.__name__} missing 'docstring'"


class TestConcreteComponentMetadata:
    """Test metadata of specific concrete components that can be instantiated."""

    @pytest.mark.parametrize("component_cls", get_concrete_test_components())
    def test_concrete_component_metadata_structure(self, component_cls):
        """Test that concrete components have well-formed metadata."""
        # Test _define_metadata() directly
        metadata = component_cls._define_metadata()
        assert isinstance(metadata, dict)
        assert "component_type" in metadata

        # Test get_metadata() includes framework fields
        full_metadata = component_cls.get_metadata()
        assert isinstance(full_metadata, dict)
        assert "class_name" in full_metadata
        assert "docstring" in full_metadata
        assert "component_type" in full_metadata
        assert full_metadata["class_name"] == component_cls.__name__

    @pytest.mark.parametrize("component_cls", get_concrete_test_components())
    def test_concrete_component_semantic_id_consistency(self, component_cls):
        """Test that semantic_id contains key metadata information."""
        metadata = component_cls.get_metadata()
        semantic_id = component_cls.semantic_id()

        # Semantic ID should contain component type
        assert metadata["component_type"] in semantic_id

        # Semantic ID should contain class name
        assert metadata["class_name"] in semantic_id


def test_no_duplicate_metadata_testing():
    """
    Ensure this comprehensive testing doesn't duplicate functionality tests.

    This test serves as documentation that:
    - This module focuses on METADATA testing only
    - Functionality tests remain in component-specific test files
    - Pipeline integration tests remain in pipeline test files
    """
    # This is a documentation test - it always passes but serves as a reminder
    # that functionality testing should happen elsewhere:

    functionality_test_locations = {
        "DataSource/DataSink functionality": "tests/test_data_io.py",
        "DataOperation functionality": "tests/test_data_processors.py",
        "Pipeline integration": "tests/test_pipeline_*.py",
        "Context processing": "tests/test_context_*.py",
    }

    # This test documents the separation of concerns
    assert len(functionality_test_locations) > 0


if __name__ == "__main__":
    # Quick diagnostic run
    print("=== Semantiva Component Metadata Diagnostic ===")

    components = get_all_semantiva_components()
    print(f"Total components found: {len(components)}")

    registry = get_component_registry()
    print(f"Component types in registry: {list(registry.keys())}")

    concrete = get_concrete_test_components()
    print(f"Concrete test components: {len(concrete)}")

    print("\nExample component metadata:")
    if concrete:
        example = next(iter(concrete))
        pprint(example.get_metadata())
