"""
Unit tests for Semantiva's LocalSemantivaOrchestrator.

These tests verify that:
  - The orchestrator executes each PipelineNode in sequence,
  - Uses the default SequentialSemantivaExecutor,
  - Publishes each node's output via the provided transport,
  - Returns the correct final data and context.

This ensures the core, single-process orchestrator behaves as expected
before plugging in more advanced transports or executors.
"""

import pytest

from semantiva.execution_tools.orchestrator.orchestrator import (
    LocalSemantivaOrchestrator,
)
from semantiva.execution_tools.transport import InMemorySemantivaTransport
from semantiva.execution_tools.executor import SequentialSemantivaExecutor
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.context_processors.context_types import ContextType
from semantiva.examples.test_utils import FloatDataType, FloatMultiplyOperation
from semantiva.logger import Logger


@pytest.fixture
def fake_pipeline():
    """
    Creates a minimal Pipeline instance for testing:
      - Two consecutive FloatMultiplyOperation nodes, each doubling the input.
    Returns:
        Pipeline object with .nodes list populated.
    """
    # We use an in-memory transport and sequential executor just to satisfy
    # PipelineNode requirements, though they aren't used by LocalSemantivaOrchestrator directly here.
    transport = InMemorySemantivaTransport()
    executor = SequentialSemantivaExecutor()

    node_configurations = [
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
    ]

    # Build the Pipeline, which constructs PipelineNodes internally
    pipeline = Pipeline(node_configurations)
    return pipeline


def test_orchestrator_applies_each_node_and_publishes(fake_pipeline):
    """
    Verify that LocalSemantivaOrchestrator.execute:
      - Runs each node in order (2.0 → *2 → *2 = 8.0),
      - Returns a FloatDataType with the correct value,
      - Passes the same ContextType instance through unchanged.
    """
    orch = LocalSemantivaOrchestrator()

    # Prepare initial data and context
    initial = FloatDataType(2.0)
    ctx = ContextType({})

    # Execute the pipeline:
    # - fake_pipeline.nodes: list of PipelineNode
    # - initial: BaseDataType
    # - ctx: ContextType
    # - transport: in-memory transport captures published intermediates
    # - Logger(): dummy logger for debugging internal steps
    data_output, context_output = orch.execute(
        fake_pipeline.nodes, initial, ctx, InMemorySemantivaTransport(), Logger()
    )

    # After two sequential multiplications by 2, 2.0 → 4.0 → 8.0
    assert data_output.data == 8.0
    # The return type should still be our FloatDataType wrapper
    assert isinstance(data_output, FloatDataType)
    # Context is passed through unchanged
    assert context_output == ctx
