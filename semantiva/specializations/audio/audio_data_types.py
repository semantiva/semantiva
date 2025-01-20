import numpy as np
from semantiva.data_types import BaseDataType


class SingleChannelAudioDataType(BaseDataType[np.ndarray]):
    """
    Represents single-channel audio data.

    This class encapsulates audio data in a single channel (mono) format, ensuring
    type consistency and providing a base for operations on such data.

    Attributes:
        _data (np.ndarray): The encapsulated single-channel audio data.
    """

    def __init__(self, data: np.ndarray, *args, **kwargs):
        """
        Initialize the SingleChannelAudioDataType with the provided data.

        Args:
            data (np.ndarray): The single-channel audio data to encapsulate.

        Raises:
            AssertionError: If the input data is not a numpy ndarray.
        """
        super().__init__(data)

    def validate(self, data):
        assert isinstance(data, np.ndarray), "Data must be a numpy ndarray."
        assert data.ndim == 1, "Data must be single channel ndarray."


class DualChannelAudioDataType(BaseDataType[np.ndarray]):
    """
    Represents dual-channel (stereo) audio data.

    This class encapsulates audio data in a dual-channel format, ensuring
    type consistency and providing a base for operations on such data.

    Attributes:
        _data (np.ndarray): The encapsulated dual-channel audio data.
    """

    def __init__(self, data: np.ndarray, *args, **kwargs):
        """
        Initialize the DualChannelAudioDataType with the provided data.

        Args:
            data (np.ndarray): The dual-channel audio data to encapsulate.

        Raises:
            AssertionError: If the input data is not a numpy ndarray.
        """
        super().__init__(data)

    def validate(self, data):
        assert isinstance(data, np.ndarray), "Data must be a numpy ndarray."
        assert data.ndim == 2, "Data must be dual channel ndarray."
