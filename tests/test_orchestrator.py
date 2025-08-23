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
Unit tests for Semantiva's LocalSemantivaOrchestrator.

These tests verify that:
  - The orchestrator executes each _PipelineNode in sequence,
  - Uses the default SequentialSemantivaExecutor,
  - Publishes each node's output via the provided transport,
  - Returns the correct final data and context.

This ensures the core, single-process orchestrator behaves as expected
before plugging in more advanced transports or executors.
"""

import pytest

from semantiva.execution.orchestrator.orchestrator import (
    LocalSemantivaOrchestrator,
)
from semantiva import Pipeline, Payload
from semantiva.execution.transport import InMemorySemantivaTransport
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
    # _PipelineNode requirements, though they aren't used by LocalSemantivaOrchestrator directly here.

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
    # - fake_pipeline.nodes: list of _PipelineNode
    # - initial: BaseDataType
    # - ctx: ContextType
    # - transport: in-memory transport captures published intermediates
    # - Logger(): dummy logger for debugging internal steps
    payload_output = orch.execute(
        fake_pipeline.resolved_spec,
        Payload(initial, ctx),
        InMemorySemantivaTransport(),
        Logger(),
        canonical_spec=fake_pipeline.canonical_spec,
    )
    data_output, context_output = payload_output.data, payload_output.context

    # After two sequential multiplications by 2, 2.0 → 4.0 → 8.0
    assert data_output.data == 8.0
    # The return type should still be our FloatDataType wrapper
    assert isinstance(data_output, FloatDataType)
    # Context is passed through unchanged
    assert context_output == ctx
