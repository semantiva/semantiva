import pytest
import numpy as np
from semantiva.specializations.audio.audio_data_types import (
    SingleChannelAudioDataType,
)
from semantiva.logger import Logger
from semantiva.payload_operations import Pipeline
from semantiva.specializations.audio.audio_operations import SingleChannelAudioOperation
from .test_audio_operation import (
    SingleChannelAudioMultiplyOperation,
    DualChannelAudioMultiplyOperation,
    SingleChannelMockDataProbe,
)


class SingleChannelAudioDummyOperation(SingleChannelAudioOperation):
    """
    A dummy operation to test pipeline inspection.
    """

    def _process_logic(self, data, mock_keyword: str):
        return data


class SingleChannelAudioDummyContextOperation(SingleChannelAudioOperation):
    """
    A dummy operation to test pipeline inspection.
    """

    def _process_logic(self, data, dummy_context: str):
        return data


@pytest.fixture
def single_channel_audio_data():
    """
    Pytest fixture for providing a SingleChannelAudioDataType instance with generated single-channel audio data.
    """
    return SingleChannelAudioDataType(np.random.rand(1000))


def test_pipeline_execution(single_channel_audio_data):
    """
    Test the execution of a pipeline with multiple nodes.

    The pipeline consists of two MultiplyAudioOperation nodes, each applying a multiplication factor.
    """
    # Define node configurations
    node_configurations = [
        {
            "operation": SingleChannelAudioMultiplyOperation,
            "parameters": {"factor": 2.0},
        },
        {
            "operation": SingleChannelAudioMultiplyOperation,
            "parameters": {"factor": 0.5},
        },
        {
            "operation": SingleChannelMockDataProbe,
        },
        {
            "operation": SingleChannelMockDataProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "operation": SingleChannelAudioDummyOperation,
        },
        {
            "operation": SingleChannelAudioDummyContextOperation,
        },
    ]

    # Create a logger instance
    logger = Logger()
    logger.set_verbose_level("DEBUG")
    logger.set_console_output()

    # Initialize the pipeline
    pipeline = Pipeline(node_configurations, logger)

    # Execute the pipeline
    output_data, output_context = pipeline.process(
        single_channel_audio_data, {"dummy_context": "dummy_context"}
    )

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
            "operation": SingleChannelAudioMultiplyOperation,
            "parameters": {"factor": 2.0},
        },
        {
            "operation": DualChannelAudioMultiplyOperation,
            "parameters": {"factor": 0.5},
        },
    ]

    # Check that initializing the pipeline raises an AssertionError
    with pytest.raises(AssertionError):
        _ = Pipeline(node_configurations)
