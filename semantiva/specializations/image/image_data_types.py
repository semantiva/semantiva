import numpy as np
from semantiva.data_types import BaseDataType, DataSequence


class ImageDataType(BaseDataType[np.ndarray]):
    """
    A class representing a 2D image data type, derived from BaseDataType.

    This class ensures that the input data is a 2D NumPy array and provides validation
    to enforce this constraint.

    Attributes:
        data (numpy.ndarray): The image data, represented as a 2D NumPy array.

    Methods:
        validate(data: numpy.ndarray):
            Validates that the input data is a 2D NumPy array.
    """

    def __init__(self, data: np.ndarray, *args, **kwargs):
        """
        Initializes the ImageDataType instance.

        Parameters:
            data (numpy.ndarray): The image data to be stored and validated.

        Raises:
            AssertionError: If the input data is not a 2D NumPy array.
        """
        super().__init__(data, *args, **kwargs)

    def validate(self, data: np.ndarray):
        """
        Validates that the input data is a 2D NumPy array.

        Parameters:
            data (numpy.ndarray): The data to validate.

        Raises:
            AssertionError: If the input data is not a NumPy array.
            AssertionError: If the input data is not a 2D array.
        """
        assert isinstance(data, np.ndarray), "Data must be a numpy ndarray."
        assert data.ndim == 2, "Data must be a 2D array."


class ImageStackDataType(DataSequence):
    """
    A class representing a stack of image data, derived from DataSequence.

    This class is designed to handle multi-dimensional image data (e.g., a stack of 2D images)
    and provides validation to ensure that the input is a NumPy array.

    Attributes:
        data (numpy.ndarray): The image stack data, represented as an N-dimensional NumPy array.

    Methods:
        validate(data: numpy.ndarray):
            Validates that the input data is an N-dimensional NumPy array.
    """

    def __init__(self, data: np.ndarray, *args, **kwargs):
        """
        Initializes the ImageStackDataType instance with the provided data.

        Parameters:
            data (numpy.ndarray): The image stack data to be stored and validated.

        Raises:
            AssertionError: If the input data is not a NumPy array.
        """
        super().__init__(data)

    def sequence_base_type(self):
        return ImageDataType

    def validate(self, data: np.ndarray):
        """
        Validates that the input data is an 3-dimensional NumPy array.

        Parameters:
            data (numpy.ndarray): The data to validate.

        Raises:
            AssertionError: If the input data is not a NumPy array.
        """
        assert isinstance(data, np.ndarray), "Data must be a numpy ndarray."
        assert data.ndim == 3, "Data must be a 3D array (stack of 2D images)"
