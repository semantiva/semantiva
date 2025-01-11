from semantic_framework.data_types import BaseDataType
import numpy as np


class SingleChannelAudioDataType(BaseDataType):
    """
    Represents single-channel audio data.

    This class encapsulates audio data in a single channel (mono) format, ensuring
    type consistency and providing a base for operations on such data.

    Attributes:
        _data (np.ndarray): The encapsulated single-channel audio data.
    """

    def __init__(self, data: np.ndarray):
        """
        Initialize the SingleChannelAudioDataType with the provided data.

        Args:
            data (np.ndarray): The single-channel audio data to encapsulate.

        Raises:
            AssertionError: If the input data is not a numpy ndarray.
        """
        assert isinstance(data, np.ndarray), "Data must be a numpy ndarray."
        self._data = data

class DualChannelAudioDataType(BaseDataType):
    """
    Represents dual-channel (stereo) audio data.

    This class encapsulates audio data in a dual-channel format, ensuring
    type consistency and providing a base for operations on such data.

    Attributes:
        _data (np.ndarray): The encapsulated dual-channel audio data.
    """

    def __init__(self, data: np.ndarray):
        """
        Initialize the DualChannelAudioDataType with the provided data.

        Args:
            data (np.ndarray): The dual-channel audio data to encapsulate.

        Raises:
            AssertionError: If the input data is not a numpy ndarray.
        """
        assert isinstance(data, np.ndarray), "Data must be a numpy ndarray."
        self._data = data