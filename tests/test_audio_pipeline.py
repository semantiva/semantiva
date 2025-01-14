import pytest
import numpy as np
from semantic_framework.specializations.audio.audio_data_types import (
    SingleChannelAudioDataType,
)
from semantic_framework.context_operations import ContextType
from semantic_framework.payload_operations import Pipeline

from test_audio_algorithm import (
    SingleChannelAudioMultiplyAlgorithm,
    DualChannelAudioMultiplyAlgorithm,
    SingleChannelMockDataProbe,
)


@pytest.fixture
def single_channel_audio_data():
    """
    Pytest fixture for providing a SingleChannelAudioDataType instance with generated single-channel audio data.
    """
    return SingleChannelAudioDataType(np.random.rand(1000))


def test_pipeline_execution(single_channel_audio_data):
    """
    Test the execution of a pipeline with multiple nodes.

    The pipeline consists of two MultiplyAudioAlgorithm nodes, each applying a multiplication factor.
    """
    # Define node configurations
    node_configurations = [
        {
            "operation": SingleChannelAudioMultiplyAlgorithm,
            "parameters": {"factor": 2.0},
        },
        {
            "operation": SingleChannelAudioMultiplyAlgorithm,
            "parameters": {"factor": 0.5},
        },
        {
            "operation": SingleChannelMockDataProbe,
        },
        {
            "operation": SingleChannelMockDataProbe,
            "context_keyword": "mock_keyword",
        },
    ]

    # Initialize the pipeline
    pipeline = Pipeline(node_configurations)

    # Execute the pipeline
    context = ContextType()
    output_data, output_context = pipeline.process(single_channel_audio_data, {})

    # Validate the output
    assert isinstance(output_data, SingleChannelAudioDataType)
    np.testing.assert_array_almost_equal(
        output_data.data, single_channel_audio_data.data * 2.0 * 0.5
    )

    print("\n")
    print("=========================Pipeline context output=========================")
    print(output_context)
    assert "mock_keyword" in output_context.keys()
    # Retrieve data collected by probes
    print("=========================Pipeline probed data=========================")
    print(pipeline.get_probe_results())
    assert "mock_keyword" in output_context.keys()
    # Inspect the pipeline
    print(
        "==============================Pipeline inspection=============================="
    )
    print(pipeline.inspect())

    # Check timers
    print(
        "================================Pipeline timers================================"
    )
    print(pipeline.get_timers())
    print(
        "==============================================================================="
    )


def test_pipeline_invalid_configuration():
    """
    Test that an invalid pipeline configuration raises an AssertionError.
    """

    # Define invalid node configurations
    node_configurations = [
        {
            "operation": SingleChannelAudioMultiplyAlgorithm,
            "parameters": {"factor": 2.0},
        },
        {
            "operation": DualChannelAudioMultiplyAlgorithm,
            "parameters": {"factor": 0.5},
        },
    ]

    # Check that initializing the pipeline raises an AssertionError
    with pytest.raises(AssertionError):
        _ = Pipeline(node_configurations)
