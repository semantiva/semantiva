import pytest
import numpy as np
from semantic_framework.specializations.audio.audio_data_types import (
    SingleChannelAudioDataType,
    DualChannelAudioDataType,
)
from semantic_framework.specializations.audio.audio_operations import (
    SingleChannelAudioAlgorithm,
)

class MultiplyAudioAlgorithm(SingleChannelAudioAlgorithm):
    """
    A specialized algorithm to multiply audio data by a given factor.
    """

    def _operation(self, data, factor):
        multiplied_data = data._data * factor
        return SingleChannelAudioDataType(multiplied_data)

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
    return SingleChannelAudioDataType(generate_single_channel_data())

@pytest.fixture
def dual_channel_audio_data():
    return DualChannelAudioDataType(generate_dual_channel_data())

def test_single_channel_data_initialization(single_channel_audio_data):
    """
    Test initialization of single-channel audio data.
    """
    assert isinstance(single_channel_audio_data._data, np.ndarray)
    assert single_channel_audio_data._data.ndim == 1

def test_dual_channel_data_initialization(dual_channel_audio_data):
    """
    Test initialization of dual-channel audio data.
    """
    assert isinstance(dual_channel_audio_data._data, np.ndarray)
    assert dual_channel_audio_data._data.ndim == 2
    assert dual_channel_audio_data._data.shape[1] == 2

def test_multiply_audio_algorithm(single_channel_audio_data):
    """
    Test MultiplyAudioAlgorithm with single-channel audio data.
    """
    factor = 2.5
    algorithm = MultiplyAudioAlgorithm()
    
    output = algorithm(single_channel_audio_data, factor)

    # Validate the algorithm's output
    assert isinstance(output, SingleChannelAudioDataType)
    assert output._data.shape == single_channel_audio_data._data.shape
    np.testing.assert_array_almost_equal(output._data, single_channel_audio_data._data * factor)
