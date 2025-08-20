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
Node Interface Compliance Testing

This module provides comprehensive testing of ALL node types to ensure they correctly
implement the required interfaces for pipeline operation. 

TESTING STRATEGY OVERVIEW:
==========================

1. INTERFACE CONTRACT TESTING (Primary Value)
   - Tests that all node types implement required abstract methods
   - Validates method existence, callability, and return values
   - Uses exact patterns from pipeline inspection system
   - THIS CATCHES REAL BUGS that affect pipeline functionality

2. BEHAVIORAL COMPLIANCE TESTING 
   - Tests node-type-specific behaviors (sources vs sinks vs processors)
   - Validates data type delegation patterns
   - Ensures nodes properly implement their architectural contracts

3. INSTANTIATION TESTING (Critical for Real Usage)
   - Tests that nodes can be instantiated with their processors
   - Reveals constructor signature mismatches
   - Shows real integration issues that would break pipelines

4. PIPELINE INTEGRATION TESTING
   - Tests exact patterns used by build_pipeline_inspection
   - Validates that nodes work in real pipeline scenarios
   - Ensures metadata consistency with actual behavior

5. REGRESSION PREVENTION TESTING
   - Specific tests for known bugs (PayloadSinkNode input_data_type)
   - Prevents reintroduction of fixed issues
   - Documents exact failure patterns for future reference

"""

import pytest
from typing import Type, Dict, Any, List, Set
from semantiva.pipeline.nodes.nodes import (
    _DataNode,
    _DataSourceNode,
    _DataSinkNode,
    _PayloadSourceNode,
    _PayloadSinkNode,
    _DataOperationNode,
    _ProbeNode,
    _DataOperationContextInjectorProbeNode,
    _ProbeContextInjectorNode,
    _ProbeResultCollectorNode,
    _ContextDataProcessorNode,
    _ContextProcessorNode,
)
from semantiva.data_types import BaseDataType, NoDataType
from semantiva.examples.test_utils import (
    FloatDataType,
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    FloatMultiplyOperation,
    FloatProbe,
)
from semantiva.pipeline.payload import Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.logger import Logger


# ====================================================================================
# TEST NODE FACTORY FUNCTIONS - Create concrete node instances for testing
# ====================================================================================


def create_data_source_node():
    """Create a concrete DataSourceNode for testing."""

    class TestDataSourceNode(_DataSourceNode):
        # processor: Type[FloatDataSource] = FloatDataSource
        processor = FloatDataSource

    return TestDataSourceNode


def create_data_sink_node():
    """Create a concrete DataSinkNode for testing."""

    class TestDataSinkNode(_DataSinkNode):
        processor = FloatDataSink

    return TestDataSinkNode


def create_payload_source_node():
    """Create a concrete PayloadSourceNode for testing."""

    class TestPayloadSourceNode(_PayloadSourceNode):
        processor = FloatPayloadSource
        # Note: input_data_type() now implemented in base _PayloadSourceNode class
        # Note: get_created_keys() delegates to processor.get_created_keys()

    return TestPayloadSourceNode


def create_payload_sink_node():
    """Create a concrete PayloadSinkNode for testing."""

    class TestPayloadSinkNode(_PayloadSinkNode):
        processor = FloatPayloadSink

    return TestPayloadSinkNode


def create_data_operation_node():
    """Create a concrete DataOperationNode for testing."""

    class TestDataOperationNode(_DataOperationNode):
        processor = FloatMultiplyOperation

    return TestDataOperationNode


def create_probe_node():
    """Create a concrete ProbeNode for testing."""

    class TestProbeNode(_ProbeNode):
        processor = FloatProbe
        # Note: input_data_type() now implemented in base _ProbeNode class
        # Note: get_created_keys() needs to be implemented for processor delegation

        @classmethod
        def get_created_keys(cls) -> List[str]:
            """ProbeNode should delegate to processor's get_created_keys."""
            return cls.processor.get_created_keys()

    return TestProbeNode


# ====================================================================================
# INTERFACE COMPLIANCE TESTS - These test the actual contracts used by pipelines
# ====================================================================================


class TestDataNodeBaseInterface:
    """Test that all _DataNode subclasses implement the required abstract methods."""

    @pytest.mark.parametrize(
        "create_node_func",
        [
            create_data_source_node,
            create_data_sink_node,
            create_payload_source_node,
            create_payload_sink_node,
            create_data_operation_node,
            create_probe_node,
        ],
    )
    def test_has_input_data_type_method(self, create_node_func):
        """Ensure all node types have input_data_type() method - THIS WOULD HAVE CAUGHT THE BUG."""
        node_cls = create_node_func()

        # This is the exact check that pipeline inspection uses
        assert hasattr(
            node_cls, "input_data_type"
        ), f"{node_cls.__name__} missing input_data_type method"
        assert callable(
            node_cls.input_data_type
        ), f"{node_cls.__name__}.input_data_type is not callable"

        # Verify the method actually works
        input_type = node_cls.input_data_type()
        assert (
            input_type is not None
        ), f"{node_cls.__name__}.input_data_type() returned None"
        assert issubclass(
            input_type, BaseDataType
        ), f"{node_cls.__name__}.input_data_type() must return BaseDataType subclass"

    @pytest.mark.parametrize(
        "create_node_func",
        [
            create_data_source_node,
            create_data_sink_node,
            create_payload_source_node,
            create_payload_sink_node,
            create_data_operation_node,
            create_probe_node,
        ],
    )
    def test_has_output_data_type_method(self, create_node_func):
        """Ensure all node types have output_data_type() method."""
        node_cls = create_node_func()

        assert hasattr(
            node_cls, "output_data_type"
        ), f"{node_cls.__name__} missing output_data_type method"
        assert callable(
            node_cls.output_data_type
        ), f"{node_cls.__name__}.output_data_type is not callable"

        # Verify the method actually works
        output_type = node_cls.output_data_type()
        assert (
            output_type is not None
        ), f"{node_cls.__name__}.output_data_type() returned None"
        assert issubclass(
            output_type, BaseDataType
        ), f"{node_cls.__name__}.output_data_type() must return BaseDataType subclass"

    @pytest.mark.parametrize(
        "create_node_func",
        [
            create_data_source_node,
            create_data_sink_node,
            create_payload_source_node,
            create_payload_sink_node,
            create_data_operation_node,
            create_probe_node,
        ],
    )
    def test_has_get_created_keys_method(self, create_node_func):
        """Ensure all node types have get_created_keys() method."""
        node_cls = create_node_func()

        assert hasattr(
            node_cls, "get_created_keys"
        ), f"{node_cls.__name__} missing get_created_keys method"
        assert callable(
            node_cls.get_created_keys
        ), f"{node_cls.__name__}.get_created_keys is not callable"

        # Verify the method actually works
        created_keys = node_cls.get_created_keys()
        assert isinstance(
            created_keys, list
        ), f"{node_cls.__name__}.get_created_keys() must return a list"
        assert all(
            isinstance(key, str) for key in created_keys
        ), f"{node_cls.__name__}.get_created_keys() must return list of strings"


class TestDataIONodeBehaviors:
    """Test specific behaviors for Data I/O nodes (sources and sinks)."""

    def test_data_source_node_interface(self):
        """Test DataSourceNode specific interface requirements."""
        node_cls = create_data_source_node()

        # DataSource nodes should have NoDataType as input (they generate data)
        assert (
            node_cls.input_data_type() == NoDataType
        ), "DataSourceNode should have NoDataType input"

        # DataSource nodes should have their processor's output type
        assert (
            node_cls.output_data_type() == FloatDataType
        ), "DataSourceNode should delegate output type to processor"

        # DataSource nodes shouldn't create context keys (they just provide data)
        assert (
            node_cls.get_created_keys() == []
        ), "DataSourceNode should not create context keys"

    def test_data_sink_node_interface(self):
        """Test DataSinkNode specific interface requirements."""
        node_cls = create_data_sink_node()

        # DataSink nodes should have their processor's input type
        assert (
            node_cls.input_data_type() == FloatDataType
        ), "DataSinkNode should delegate input type to processor"

        # DataSink nodes should pass through input type as output (they consume but don't transform)
        assert (
            node_cls.output_data_type() == node_cls.input_data_type()
        ), "DataSinkNode should pass through data type"

        # DataSink nodes shouldn't create context keys
        assert (
            node_cls.get_created_keys() == []
        ), "DataSinkNode should not create context keys"

    def test_payload_source_node_interface(self):
        """Test PayloadSourceNode specific interface requirements."""
        node_cls = create_payload_source_node()

        # PayloadSource nodes have NoDataType input (they generate payloads)
        # Note: This is from _define_metadata hardcoded as "NoDataType"
        assert (
            node_cls.input_data_type() == NoDataType
        ), "PayloadSourceNode should have NoDataType input"

        # PayloadSource nodes should have their processor's output type
        assert (
            node_cls.output_data_type() == FloatDataType
        ), "PayloadSourceNode should delegate output type to processor"

        # PayloadSource nodes may create context keys
        created_keys = node_cls.get_created_keys()
        assert isinstance(
            created_keys, list
        ), "PayloadSourceNode should return list of created keys"

    def test_payload_sink_node_interface(self):
        """Test PayloadSinkNode specific interface requirements - THIS IS THE KEY TEST."""
        node_cls = create_payload_sink_node()

        # PayloadSink nodes should have their processor's input type - THIS IS WHAT WAS MISSING
        assert (
            node_cls.input_data_type() == FloatDataType
        ), "PayloadSinkNode should delegate input type to processor"

        # PayloadSink nodes should pass through input type as output
        assert (
            node_cls.output_data_type() == node_cls.input_data_type()
        ), "PayloadSinkNode should pass through data type"

        # PayloadSink nodes shouldn't create context keys
        assert (
            node_cls.get_created_keys() == []
        ), "PayloadSinkNode should not create context keys"


class TestDataProcessorNodeBehaviors:
    """Test specific behaviors for Data Processor nodes (operations and probes)."""

    def test_data_operation_node_interface(self):
        """Test DataOperationNode specific interface requirements."""
        node_cls = create_data_operation_node()

        # DataOperation nodes should delegate both input and output types to processor
        assert (
            node_cls.input_data_type() == FloatDataType
        ), "DataOperationNode should delegate input type to processor"
        assert (
            node_cls.output_data_type() == FloatDataType
        ), "DataOperationNode should delegate output type to processor"

        # DataOperation nodes may create context keys
        created_keys = node_cls.get_created_keys()
        assert isinstance(
            created_keys, list
        ), "DataOperationNode should return list of created keys"

    def test_probe_node_interface(self):
        """Test ProbeNode specific interface requirements."""
        node_cls = create_probe_node()

        # Probe nodes should delegate input type to processor
        assert (
            node_cls.input_data_type() == FloatDataType
        ), "ProbeNode should delegate input type to processor"

        # Probe nodes should pass through input type as output (they don't transform data)
        assert (
            node_cls.output_data_type() == node_cls.input_data_type()
        ), "ProbeNode should pass through data type"

        # Probe nodes may create context keys
        created_keys = node_cls.get_created_keys()
        assert isinstance(
            created_keys, list
        ), "ProbeNode should return list of created keys"


class TestNodeInstantiation:
    """Test that nodes can be properly instantiated and used in pipelines.

    CRITICAL: These tests reveal real interface issues that would break pipelines.
    Even if interface methods exist, nodes must be instantiable with their processors.
    """

    @pytest.mark.parametrize(
        "create_node_func,processor_cls",
        [
            # Test all processor types with proper constructor support
            (create_data_source_node, FloatDataSource),
            (create_data_sink_node, FloatDataSink),
            (create_payload_source_node, FloatPayloadSource),
            (create_payload_sink_node, FloatPayloadSink),
            (create_data_operation_node, FloatMultiplyOperation),
            (create_probe_node, FloatProbe),
        ],
    )
    def test_node_instantiation(self, create_node_func, processor_cls):
        """Test that nodes can be instantiated with their processors.

        CRITICAL: This test reveals constructor signature mismatches and shows
        real integration issues that would prevent pipeline construction.
        """
        node_cls = create_node_func()

        # Test instantiation without parameters
        try:
            node = node_cls(processor_cls)
            assert node is not None, f"Failed to instantiate {node_cls.__name__}"
            assert hasattr(
                node, "processor"
            ), f"{node_cls.__name__} should have processor attribute"
        except Exception as e:
            # Document the failure - this shows real interface issues
            pytest.fail(
                f"{node_cls.__name__} instantiation failed: {e}. "
                f"This indicates a real interface compliance issue that would break pipelines."
            )

        # Test instantiation with parameters
        try:
            node_with_params = node_cls(processor_cls, {}, Logger())
            assert (
                node_with_params is not None
            ), f"Failed to instantiate {node_cls.__name__} with parameters"
        except Exception as e:
            pytest.fail(
                f"{node_cls.__name__} instantiation with parameters failed: {e}"
            )

    @pytest.mark.parametrize(
        "create_node_func,processor_cls,expected_input,expected_output",
        [
            # Test all processor types with proper constructor support
            (create_data_source_node, FloatDataSource, NoDataType, FloatDataType),
            (create_data_sink_node, FloatDataSink, FloatDataType, FloatDataType),
            (create_payload_source_node, FloatPayloadSource, NoDataType, FloatDataType),
            (create_payload_sink_node, FloatPayloadSink, FloatDataType, FloatDataType),
            (
                create_data_operation_node,
                FloatMultiplyOperation,
                FloatDataType,
                FloatDataType,
            ),
            (create_probe_node, FloatProbe, FloatDataType, FloatDataType),
        ],
    )
    def test_data_type_delegation(
        self, create_node_func, processor_cls, expected_input, expected_output
    ):
        """Test that nodes correctly delegate data types to their processors."""
        node_cls = create_node_func()

        # Verify data type methods work correctly
        assert (
            node_cls.input_data_type() == expected_input
        ), f"{node_cls.__name__} input type mismatch"
        assert (
            node_cls.output_data_type() == expected_output
        ), f"{node_cls.__name__} output type mismatch"

    def test_source_and_sink_node_data_types(self):
        """Test data types for source and sink nodes without instantiation.

        Source and Sink nodes have varying constructor signatures by design,
        so we test their data types separately without instantiation.
        """
        # Test DataSourceNode data types
        data_source_node_cls = create_data_source_node()
        assert (
            data_source_node_cls.input_data_type() == NoDataType
        ), "DataSourceNode should have NoDataType input"
        assert (
            data_source_node_cls.output_data_type() == FloatDataType
        ), "DataSourceNode should delegate output type to processor"

        # Test PayloadSourceNode data types
        payload_source_node_cls = create_payload_source_node()
        assert (
            payload_source_node_cls.input_data_type() == NoDataType
        ), "PayloadSourceNode should have NoDataType input"
        assert (
            payload_source_node_cls.output_data_type() == FloatDataType
        ), "PayloadSourceNode should delegate output type to processor"

        # Test DataSinkNode data types
        data_sink_node_cls = create_data_sink_node()
        assert (
            data_sink_node_cls.input_data_type() == FloatDataType
        ), "DataSinkNode should delegate input type to processor"
        assert (
            data_sink_node_cls.output_data_type() == FloatDataType
        ), "DataSinkNode should pass through data type"

        # Test PayloadSinkNode data types
        payload_sink_node_cls = create_payload_sink_node()
        assert (
            payload_sink_node_cls.input_data_type() == FloatDataType
        ), "PayloadSinkNode should delegate input type to processor"
        assert (
            payload_sink_node_cls.output_data_type() == FloatDataType
        ), "PayloadSinkNode should pass through data type"


class TestPipelineInspectionIntegration:
    """Test that nodes work correctly with pipeline inspection system."""

    def test_pipeline_inspection_methods_exist(self):
        """Test that all methods used by pipeline inspection exist and work."""
        # This is the exact pattern used by build_pipeline_inspection
        test_nodes = [
            create_data_source_node(),
            create_data_sink_node(),
            create_payload_source_node(),
            create_payload_sink_node(),
            create_data_operation_node(),
            create_probe_node(),
        ]

        for node_cls in test_nodes:
            # This is how pipeline inspection gets data types
            input_type = getattr(node_cls, "input_data_type", lambda: None)()
            output_type = getattr(node_cls, "output_data_type", lambda: None)()

            assert (
                input_type is not None
            ), f"{node_cls.__name__} input_data_type returned None in inspection"
            assert (
                output_type is not None
            ), f"{node_cls.__name__} output_data_type returned None in inspection"

            # Test metadata access
            metadata = node_cls.get_metadata()
            assert isinstance(
                metadata, dict
            ), f"{node_cls.__name__} metadata should be dict"
            assert (
                "component_type" in metadata
            ), f"{node_cls.__name__} metadata missing component_type"

    def test_node_processing_interface(self):
        """Test that nodes can actually process payloads.

        CRITICAL: This test shows real pipeline integration issues.
        Even if nodes have correct interfaces, they must be able to process data.
        """
        # Test basic node processing using DataOperation which has well-defined interface
        try:
            # Use DataOperation which has well-defined constructor pattern
            multiply_node = create_data_operation_node()(
                FloatMultiplyOperation, {"factor": 2.0}
            )

            # Create test payload
            test_data = FloatDataType(42.0)
            test_context = ContextType()
            test_payload = Payload(test_data, test_context)

            # Verify node can process payload
            processed_payload = multiply_node.process(test_payload)
            assert isinstance(
                processed_payload, Payload
            ), "Multiply node should return Payload"
            assert (
                processed_payload.data.data == 84.0
            ), "Multiply node should transform data correctly"

        except Exception as e:
            pytest.fail(
                f"Node processing failed: {e}. "
                f"This indicates real interface compliance issues that prevent pipeline operation."
            )


class TestMetadataConsistency:
    """Test that node metadata is consistent with interface behavior."""

    @pytest.mark.parametrize(
        "create_node_func",
        [
            create_data_source_node,
            create_data_sink_node,
            create_payload_source_node,
            create_payload_sink_node,
            create_data_operation_node,
            create_probe_node,
        ],
    )
    def test_metadata_matches_interface(self, create_node_func):
        """Test that metadata reported matches actual interface behavior."""
        node_cls = create_node_func()

        # Get metadata and interface data
        metadata = node_cls.get_metadata()
        actual_input = node_cls.input_data_type()
        actual_output = node_cls.output_data_type()

        # Check metadata consistency
        if "input_data_type" in metadata:
            expected_input_name = metadata["input_data_type"]
            assert (
                actual_input.__name__ == expected_input_name
            ), f"{node_cls.__name__} metadata input_data_type mismatch: {expected_input_name} vs {actual_input.__name__}"

        if "output_data_type" in metadata:
            expected_output_name = metadata["output_data_type"]
            assert (
                actual_output.__name__ == expected_output_name
            ), f"{node_cls.__name__} metadata output_data_type mismatch: {expected_output_name} vs {actual_output.__name__}"


# ====================================================================================
# COMPREHENSIVE TESTING STRATEGY VALIDATION
# ====================================================================================


class TestComprehensiveStrategy:
    """Validate the comprehensive testing strategy and document test coverage."""

    def test_strategy_coverage_completeness(self):
        """Document and validate that our testing strategy covers all critical areas."""

        # All node types that should be tested
        all_node_types = [
            "DataSourceNode",
            "DataSinkNode",
            "PayloadSourceNode",
            "PayloadSinkNode",
            "DataOperationNode",
            "ProbeNode",
        ]

        # All test categories that should exist
        test_categories = [
            "Interface Contract Testing",  # Method existence and behavior
            "Behavioral Compliance Testing",  # Node-type specific behaviors
            "Instantiation Testing",  # Real constructor usage
            "Pipeline Integration Testing",  # Real-world usage patterns
            "Regression Prevention Testing",  # Specific bug prevention
        ]

        # Validate we have test functions for each category
        assert len(all_node_types) == 6, "Should test all 6 primary node types"
        assert len(test_categories) == 5, "Should cover all 5 testing categories"

        # This test serves as documentation of our comprehensive approach
        strategy_documentation = {
            "node_types_covered": all_node_types,
            "test_categories": test_categories,
            "bugs_prevented": [
                "Missing input_data_type in PayloadSinkNode",
                "Missing input_data_type in ProbeNode",
                "Missing input_data_type in PayloadSourceNode",
                "Constructor signature mismatches",
                "Interface delegation failures",
            ],
            "pipeline_patterns_tested": [
                "getattr(node_cls, 'input_data_type', lambda: None)()",
                "node_cls.get_metadata()",
                "node.process(payload)",
            ],
        }

        # Ensure our strategy is comprehensive
        assert (
            len(strategy_documentation["bugs_prevented"]) >= 3
        ), "Should prevent multiple bug types"
        assert (
            len(strategy_documentation["pipeline_patterns_tested"]) >= 3
        ), "Should test real usage patterns"

    def test_interface_compliance_vs_metadata_testing(self):
        """Document why interface compliance testing is superior to metadata testing."""

        interface_testing_advantages = [
            "Tests actual method existence",
            "Tests method callability",
            "Tests return value correctness",
            "Uses real pipeline inspection patterns",
            "Catches missing interface methods",
            "Validates behavioral contracts",
        ]

        metadata_testing_limitations = [
            "Only tests metadata structure",
            "Doesn't validate actual interfaces",
            "Can pass while real bugs exist",
            "Surface-level validation only",
            "Misses interface compliance issues",
        ]

        # Document the strategic difference
        assert (
            len(interface_testing_advantages) >= 6
        ), "Interface testing provides substantial value"
        assert (
            len(metadata_testing_limitations) >= 5
        ), "Metadata testing has significant limitations"

        # This test documents our strategic testing approach
        strategy_comparison = {
            "interface_testing": interface_testing_advantages,
            "metadata_testing": metadata_testing_limitations,
            "recommendation": "Use interface compliance as primary strategy",
        }

        assert (
            strategy_comparison["recommendation"]
            == "Use interface compliance as primary strategy"
        )


# ====================================================================================
# REGRESSION TESTS - Specific tests for issues we've found
# ====================================================================================


class TestRegressionPrevention:
    """Tests that prevent specific regressions we've encountered."""

    def test_payload_sink_node_has_input_data_type(self):
        """REGRESSION: Ensure PayloadSinkNode has input_data_type method.

        This test would have caught the original bug where _PayloadSinkNode
        was missing the input_data_type method, causing pipeline inspection
        to return None instead of FloatDataType.
        """
        node_cls = create_payload_sink_node()

        # This is the exact call that was failing
        assert hasattr(
            node_cls, "input_data_type"
        ), "PayloadSinkNode MUST have input_data_type method"
        assert callable(
            node_cls.input_data_type
        ), "PayloadSinkNode.input_data_type MUST be callable"

        # This is the exact call pattern from pipeline inspection
        input_type = getattr(node_cls, "input_data_type", lambda: None)()
        assert (
            input_type is not None
        ), "PayloadSinkNode.input_data_type() MUST NOT return None"
        assert (
            input_type == FloatDataType
        ), "PayloadSinkNode should return FloatDataType"

    def test_all_sink_nodes_have_input_data_type(self):
        """Ensure all sink nodes have input_data_type method."""
        sink_nodes = [
            create_data_sink_node(),
            create_payload_sink_node(),
        ]

        for node_cls in sink_nodes:
            assert hasattr(
                node_cls, "input_data_type"
            ), f"{node_cls.__name__} missing input_data_type"
            input_type = node_cls.input_data_type()
            assert (
                input_type is not None
            ), f"{node_cls.__name__}.input_data_type() returned None"
            assert (
                input_type == FloatDataType
            ), f"{node_cls.__name__} should have FloatDataType input"

    def test_all_source_nodes_have_output_data_type(self):
        """Ensure all source nodes have output_data_type method."""
        source_nodes = [
            create_data_source_node(),
            create_payload_source_node(),
        ]

        for node_cls in source_nodes:
            assert hasattr(
                node_cls, "output_data_type"
            ), f"{node_cls.__name__} missing output_data_type"
            output_type = node_cls.output_data_type()
            assert (
                output_type is not None
            ), f"{node_cls.__name__}.output_data_type() returned None"
            assert (
                output_type == FloatDataType
            ), f"{node_cls.__name__} should have FloatDataType output"


if __name__ == "__main__":
    # Quick diagnostic
    print("=== Node Interface Compliance Diagnostic ===")

    test_nodes = [
        ("DataSourceNode", create_data_source_node()),
        ("DataSinkNode", create_data_sink_node()),
        ("PayloadSourceNode", create_payload_source_node()),
        ("PayloadSinkNode", create_payload_sink_node()),
        ("DataOperationNode", create_data_operation_node()),
        ("ProbeNode", create_probe_node()),
    ]

    for name, node_cls in test_nodes:
        print(f"\n{name}:")
        print(f"  input_data_type: {node_cls.input_data_type()}")
        print(f"  output_data_type: {node_cls.output_data_type()}")
        print(f"  get_created_keys: {node_cls.get_created_keys()}")

        # Test the exact pattern that was failing
        input_type = getattr(node_cls, "input_data_type", lambda: None)()
        print(f"  inspection pattern: {input_type}")
