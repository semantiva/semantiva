# tests/execution_tools/test_orchestrator.py

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
    transport = InMemorySemantivaTransport()
    executor = SequentialSemantivaExecutor()

    # Mimic a minimal pipeline interface
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
    orch = LocalSemantivaOrchestrator()
    initial = FloatDataType(2.0)
    ctx = ContextType({})
    data_output, context_output = orch.execute(
        fake_pipeline.nodes, initial, ctx, InMemorySemantivaTransport(), Logger()
    )
    assert data_output.data == 8.0
    assert isinstance(data_output, FloatDataType)
    assert context_output == ctx
