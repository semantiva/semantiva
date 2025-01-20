import pytest
import numpy as np
from semantiva.specializations.audio.audio_data_types import (
    SingleChannelAudioDataType,
    DualChannelAudioDataType,
)
from semantiva.specializations.audio.audio_operations import (
    SingleChannelAudioAlgorithm,
    SingleChannelAudioProbe,
    DualChannelAudioAlgorithm,
)

from semantiva.payload_operations import node_factory
from semantiva.context_operations.context_types import ContextType


class SingleChannelAudioMultiplyAlgorithm(SingleChannelAudioAlgorithm):
    """
    A specialized algorithm to multiply single-channel audio data by a given factor.
    """

    def _operation(self, data, factor):
        multiplied_data = data.data * factor
        return SingleChannelAudioDataType(multiplied_data)


class DualChannelAudioMultiplyAlgorithm(DualChannelAudioAlgorithm):
    """
    A specialized algorithm to multiply each channel of dual-channel audio data
    by a given factor, reusing SingleChannelAudioMultiplyAlgorithm.
    """

    def _operation(self, data, factor):
        left_channel = SingleChannelAudioDataType(data.data[:, 0])
        right_channel = SingleChannelAudioDataType(data.data[:, 1])

        single_channel_multiplier = SingleChannelAudioMultiplyAlgorithm()

        left_result = single_channel_multiplier(left_channel, factor)
        right_result = single_channel_multiplier(right_channel, factor)

        multiplied_data = np.column_stack((left_result.data, right_result.data))
        return DualChannelAudioDataType(multiplied_data)


class SingleChannelAudioMockContextInjectorAlgorithm(SingleChannelAudioAlgorithm):
    """
    Mock algorithm to test injection of context values.
    """

    def context_keys(self):
        return ["dummy_key"]

    def _operation(self, data, factor):
        multiplied_data = data.data * factor
        self._notify_context_update("dummy_key", factor)
        return SingleChannelAudioDataType(multiplied_data)


class SingleChannelMockDataProbe(SingleChannelAudioProbe):
    """
    A probe to retrieve the duration (length) of single-channel audio data.
    """

    def _operation(self, data, *args, **kwargs) -> int:
        return len(data.data)


def generate_single_channel_data(length=1000):
    """
    Generate synthetic single-channel audio data.
    """
    return np.random.rand(length)


def generate_dual_channel_data(length=1000):
    """
    Generate synthetic dual-channel audio data.
    """
    return np.random.rand(length, 2)


@pytest.fixture
def single_channel_audio_data():
    """
    Pytest fixture for providing a SingleChannelAudioDataType instance with generated single-channel audio data.
    """
    return SingleChannelAudioDataType(generate_single_channel_data())


@pytest.fixture
def dual_channel_audio_data():
    """
    Pytest fixture for providing a DualChannelAudioDataType instance with generated dual-channel audio data.
    """
    return DualChannelAudioDataType(generate_dual_channel_data())


def test_single_channel_data_initialization(single_channel_audio_data):
    """
    Test initialization of single-channel audio data.
    """
    assert isinstance(single_channel_audio_data.data, np.ndarray)
    assert single_channel_audio_data.data.ndim == 1


def test_dual_channel_data_initialization(dual_channel_audio_data):
    """
    Test initialization of dual-channel audio data.
    """
    assert isinstance(dual_channel_audio_data.data, np.ndarray)
    assert dual_channel_audio_data.data.ndim == 2
    assert dual_channel_audio_data.data.shape[1] == 2


def test_single_channel_multiply_algorithm(single_channel_audio_data):
    """
    Test SingleChannelAudioMultiplyAlgorithm with single-channel audio data.
    """
    factor = 2.5
    algorithm = SingleChannelAudioMultiplyAlgorithm()

    output = algorithm(single_channel_audio_data, factor)

    # Validate the algorithm's output
    assert isinstance(output, SingleChannelAudioDataType)
    assert output.data.shape == single_channel_audio_data.data.shape
    np.testing.assert_array_almost_equal(
        output.data, single_channel_audio_data.data * factor
    )


def test_single_channel_context_notification_algorithm(single_channel_audio_data):
    """
    Test SingleChannelAudioMockContextInjectorAlgorithm with single-channel audio data.
    """

    # Define the node configuration
    node_configuration = {
        "operation": SingleChannelAudioMockContextInjectorAlgorithm,
        "parameters": {"factor": 2.5},
    }

    # Create the algorithm node using the node factory
    algorithm_node = node_factory(node_configuration)

    # Initialize the context and process the data
    context = ContextType()
    output, updated_context = algorithm_node.process(single_channel_audio_data, context)

    # Validate the algorithm's output
    assert isinstance(output, SingleChannelAudioDataType)
    assert output.data.shape == single_channel_audio_data.data.shape
    np.testing.assert_array_almost_equal(
        output.data, single_channel_audio_data.data * 2.5
    )

    # Validate the context update
    assert (
        updated_context.get_value("dummy_key")
        == node_configuration["parameters"]["factor"]
    )


def test_dual_channel_multiply_algorithm(dual_channel_audio_data):
    """
    Test DualChannelAudioMultiplyAlgorithm with dual-channel audio data.
    """
    factor = 2.5
    algorithm = DualChannelAudioMultiplyAlgorithm()

    output = algorithm(dual_channel_audio_data, factor)

    # Validate the algorithm's output
    assert isinstance(output, DualChannelAudioDataType)
    assert output.data.shape == dual_channel_audio_data.data.shape
    np.testing.assert_array_almost_equal(
        output.data, dual_channel_audio_data.data * factor
    )


def test_single_channel_data_probe_duration(single_channel_audio_data):
    """
    Test SingleChannelDataProbe to verify it returns the duration of the audio.
    """

    # Instantiate the probe
    probe = SingleChannelMockDataProbe()

    # Execute the probe on single-channel audio data
    duration = probe(single_channel_audio_data)

    # Validate the output
    assert isinstance(duration, int)
    assert duration == len(single_channel_audio_data.data)
