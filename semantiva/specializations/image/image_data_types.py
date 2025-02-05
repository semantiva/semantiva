import numpy as np
from typing import Iterator, Optional
from semantiva.data_types import BaseDataType, DataCollectionType


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
        assert isinstance(
            data, np.ndarray
        ), f"Data must be a numpy ndarray, got {type(data)}."
        assert data.ndim == 2, "Data must be a 2D array."
        return data

    def __str__(self):
        return f"ImageDataType: {self.data.shape}"


class ImageStackDataType(DataCollectionType[ImageDataType, np.ndarray]):
    """
    A class representing a stack of image data, derived from DataCollection.

    This class is designed to handle multi-dimensional image data (e.g., a stack of 2D images)
    and provides validation to ensure that the input is a NumPy array.

    Attributes:
        data (numpy.ndarray): The image stack data, represented as an N-dimensional NumPy array.

    Methods:
        validate(data: numpy.ndarray):
            Validates that the input data is an N-dimensional NumPy array.
    """

    def __init__(self, data: Optional[np.ndarray] = None):
        """
        Initializes the ImageStackDataType instance.

        Args:
            data (Optional[np.ndarray]): The image stack data to be stored and validated.
        """
        super().__init__(data)

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

    def __iter__(self) -> Iterator[ImageDataType]:
        """Iterates through the 3D NumPy array, treating each 2D slice as an ImageDataType."""
        for i in range(self._data.shape[0]):
            yield ImageDataType(self._data[i])

    def append(self, item: ImageDataType) -> None:
        """
        Appends a 2D image to the image stack.

        This method takes an `ImageDataType` instance and adds its underlying 2D NumPy array
        to the existing 3D NumPy stack. If the stack is empty, it initializes it with the new image.

        Args:
            item (ImageDataType): The 2D image to append.

        Raises:
            TypeError: If the item is not an instance of `ImageDataType`.
            ValueError: If the image dimensions do not match the existing stack.
        """
        if not isinstance(item, ImageDataType):
            raise TypeError(f"Expected ImageDataType, got {type(item)}")

        new_image = item.data  # Extract the 2D NumPy array

        if not isinstance(new_image, np.ndarray) or new_image.ndim != 2:
            raise ValueError(f"Expected a 2D NumPy array, got shape {new_image.shape}")

        # If the stack is empty, initialize with the first image
        if self._data.size == 0:
            self._data = np.expand_dims(
                new_image, axis=0
            )  # Convert 2D to 3D with shape (1, H, W)
        else:
            # Ensure the new image has the same dimensions as existing ones
            if new_image.shape != self._data.shape[1:]:
                raise ValueError(
                    f"Image dimensions {new_image.shape} do not match existing stack {self._data.shape[1:]}"
                )

            # Append along the first axis (stack dimension)
            self._data = np.concatenate(
                (self._data, np.expand_dims(new_image, axis=0)), axis=0
            )

    @classmethod
    def _initialize_empty(cls) -> np.ndarray:
        """
        Returns an empty 3D NumPy array for initializing an empty ImageStackDataType.
        """
        return np.empty((0, 0, 0))  # Empty 3D array

    def __len__(self) -> int:
        """
        Returns the number of images in the stack.

        This method returns the number of 2D images stored along the first axis of
        the 3D NumPy array.

        Returns:
            int: The number of images in the stack.
        """
        return self._data.shape[0]

    def __str__(self):
        return f"ImageStackDataType: {self._data.shape}"
