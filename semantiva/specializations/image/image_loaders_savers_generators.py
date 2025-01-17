from PIL import Image
import numpy as np
from semantiva.context_operations.context_types import ContextType
from .image_data_io import (
    ImageDataSource,
    ImageStackSource,
    ImageDataSink,
    ImageStackDataSink,
    ImagePayloadSink,
    ImageStackPayloadSource,
)
from .image_data_types import ImageDataType, ImageStackDataType


class NpzImageDataTypeLoader(ImageDataSource):
    """
    Concrete implementation of ImageDataTypeSource for loading image data from .npz files.

    This class provides functionality to load a single array from a `.npz` file
    as an `ImageDataType`.
    """

    def _get_data(self, path: str) -> ImageDataType:
        """
        Loads the single array from a .npz file and returns it as an `ImageDataType`.

        Assumes the `.npz` file contains only one array.

        Parameters:
            path (str): The path to the .npz file containing the image data.

        Returns:
            ImageDataType: The loaded image data.

        Raises:
            FileNotFoundError: If the file at the specified path does not exist.
            ValueError: If the .npz file does not contain exactly one array.
            ValueError: If the array is not a 2D array.
        """
        try:
            # Load the .npz file
            with np.load(path) as data:
                # Validate the file contains exactly one array
                if len(data.files) != 1:
                    raise ValueError(
                        f"The file {path} must contain exactly one array, but found {len(data.files)}."
                    )

                # Get the array
                array_name = data.files[0]
                array = data[array_name]

                # Validate the array shape
                if array.ndim != 2:
                    raise ValueError(f"The array in {path} is not a 2D array.")

                # Wrap the array in an ImageDataType object
                return ImageDataType(array)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {path}") from e
        except Exception as e:
            raise ValueError(f"Error loading image data from {path}: {e}") from e


class NpzImageDataSaver(ImageDataSink):
    """
    Concrete implementation of ImageDataTypeSink for saving `ImageDataType` objects to .npz files.

    This class provides functionality to save an `ImageDataType` object into a `.npz` file.
    """

    def _send_data(self, data: ImageDataType, path: str):
        """
        Saves the `ImageDataType` as a `.npz` file at the specified path.

        Parameters:
            data (ImageDataType): The image data to be saved.
            path (str): The file path to save the `.npz` file.

        Raises:
            ValueError: If the provided data is not an `ImageDataType`.
            IOError: If the file cannot be saved.
        """
        if not isinstance(data, self.input_data_type()):
            raise ValueError("Provided data is not an instance of ImageDataType.")

        try:
            # Save the data to an .npz file
            np.savez(path, image=data.data)
        except Exception as e:
            raise IOError(f"Error saving ImageDataType to {path}: {e}") from e


class NpzImageStackDataLoader(ImageStackSource):
    """
    Concrete implementation of ImageStackDataTypeSource for loading image stack data from .npz files.

    This class provides functionality to load a single 3D array from a `.npz` file
    as an `ImageStackDataType`.
    """

    def _get_data(self, path: str) -> ImageStackDataType:
        """
        Loads the single 3D array from a .npz file and returns it as an `ImageStackDataType`.

        Assumes the `.npz` file contains only one array, which is 3D.

        Parameters:
            path (str): The path to the .npz file containing the image stack data.

        Returns:
            ImageStackDataType: The loaded image stack data.

        Raises:
            FileNotFoundError: If the file at the specified path does not exist.
            ValueError: If the .npz file does not contain exactly one array.
            ValueError: If the array is not a 3D array.
        """
        try:
            # Load the .npz file
            with np.load(path) as data:
                # Validate the file contains exactly one array
                if len(data.files) != 1:
                    raise ValueError(
                        f"The file {path} must contain exactly one array, but found {len(data.files)}."
                    )

                # Get the array
                array_name = data.files[0]
                array = data[array_name]

                # Validate that it a 3D array
                if array.ndim != 3:
                    raise ValueError(f"The array in {path} is not a 3D array.")

                # Wrap the array in an ImageStackDataType object
                return ImageStackDataType(array)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {path}") from e
        except Exception as e:
            raise ValueError(f"Error loading image stack data from {path}: {e}") from e


class NpzImageStackDataSaver(ImageStackDataSink):
    """
    Concrete implementation of ImageStackDataTypeSink for saving `ImageStackDataType` objects to .npz files.

    This class provides functionality to save an `ImageStackDataType` object into a `.npz` file.
    """

    def _send_data(self, data: ImageStackDataType, path: str):
        """
        Saves the `ImageStackDataType` as a `.npz` file at the specified path.

        Parameters:
            data (ImageStackDataType): The image stack data to be saved.
            path (str): The file path to save the `.npz` file.

        Raises:
            ValueError: If the provided data is not an `ImageStackDataType`.
            IOError: If the file cannot be saved.
        """
        if not isinstance(data, self.input_data_type()):
            raise ValueError("Provided data is not an instance of ImageStackDataType.")

        try:
            # Save the data to an .npz file
            np.savez(path, image_stack=data.data)
        except Exception as e:
            raise IOError(f"Error saving ImageStackDataType to {path}: {e}") from e


class PngImageLoader(ImageDataSource):
    """
    Concrete implementation of ImageDataTypeSource for loading image data from PNG files.

    This class provides functionality to load a PNG image as an `ImageDataType`.
    """

    def _get_data(self, path: str) -> ImageDataType:
        """
        Loads a PNG image from the specified file path and returns it as an `ImageDataType`.

        Parameters:
            path (str): The path to the PNG file.

        Returns:
            ImageDataType: The loaded image data.

        Raises:
            FileNotFoundError: If the file at the specified path does not exist.
            ValueError: If the file cannot be opened or does not contain valid image data.
        """
        try:
            # Open the PNG image
            with Image.open(path) as img:
                # Convert the image to grayscale and load it as a NumPy array
                image_array = np.asarray(img.convert("L"))
                # Wrap the array in an ImageDataType object
                return ImageDataType(image_array)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {path}") from e
        except Exception as e:
            raise ValueError(f"Error loading PNG image from {path}: {e}") from e


class PngImageSaver(ImageDataSink):
    """
    Concrete implementation of ImageDataTypeSink for saving image data to PNG files.

    This class provides functionality to save an `ImageDataType` object as a PNG image.
    """

    def _send_data(self, data: ImageDataType, path: str):
        """
        Saves the `ImageDataType` as a PNG file at the specified path.

        Parameters:
            data (ImageDataType): The image data to be saved.
            path (str): The file path to save the PNG image.

        Raises:
            ValueError: If the provided data is not an `ImageDataType`.
            IOError: If the file cannot be saved.
        """
        if not isinstance(
            data, self.input_data_type()
        ):  # Check if the data type is correct
            raise ValueError("Provided data is not an instance of ImageDataType.")

        try:
            # Convert the NumPy array to a PIL image
            img = Image.fromarray(data.data.astype(np.uint8))
            # Save the image as a PNG
            img.save(path, format="PNG")
        except Exception as e:
            raise IOError(f"Error saving PNG image to {path}: {e}") from e


class ImageDataRandomGenerator(ImageDataSource):
    """
    A random generator for creating `ImageDataType` objects with random data.

    This class is used to generate dummy image data for testing and development purposes.
    The generated data is a 2D NumPy array of random values between 0 and 1, wrapped in an
    `ImageDataType` object.

    Methods:
        _get_data(shape: tuple[int, int]) -> ImageDataType:
            Generates a dummy `ImageDataType` with the specified shape.
    """

    def _get_data(self, shape: tuple[int, int]) -> ImageDataType:
        """
        Generates a dummy `ImageDataType` with random values.

        Parameters:
            shape (tuple[int, int]): The shape (rows, columns) of the generated image data.

        Returns:
            ImageDataType: A dummy image data object containing a 2D array of random values.

        Raises:
            ValueError: If the provided shape does not have exactly two dimensions.
        """

        # Validate that the shape represents a 2D array
        if len(shape) != 2:
            raise ValueError(
                f"Shape must be a tuple with two dimensions, but got {shape}."
            )
        return ImageDataType(np.random.rand(*shape))


class ImageStackRandomGenerator(ImageStackSource):
    """
    A random generator for creating `ImageStackDataType` objects with random data.

    This class is used to generate dummy image stack data for testing and development purposes.
    The generated data is a 3D NumPy array of random values between 0 and 1, wrapped in an
    `ImageStackDataType` object.

    Methods:
        _get_data(shape: tuple[int, int, int]) -> ImageStackDataType:
            Generates a dummy `ImageStackDataType` with the specified shape.
    """

    def _get_data(self, shape: tuple[int, int, int]) -> ImageStackDataType:
        """
        Generates a dummy `ImageStackDataType` with random values.

        Parameters:
            shape (tuple[int, int, int]): The shape (slices, rows, columns) of the generated
                                          image stack data.

        Returns:
            ImageStackDataType: A dummy image stack data object containing a 3D array of random values.

        Raises:
            ValueError: If the provided shape does not have exactly three dimensions.
        """
        # Validate that the shape represents a 3D array
        if len(shape) != 3:
            raise ValueError(
                f"Shape must be a tuple with three dimensions, but got {shape}."
            )

        return ImageStackDataType(np.random.rand(*shape))


class ImageStackPayloadRandomGenerator(ImageStackPayloadSource):
    """
    A random generator for producing payloads containing ImageStackDataType and ContextType.

    This class generates dummy payloads for testing purposes or as a placeholder
    in pipelines where input data is not yet available. The generated payloads
    contain an `ImageStackDataType` object with random or placeholder data and an
    associated `ContextType`.

    Methods:
        get_payload(*args, **kwargs) -> tuple[ImageStackDataType, ContextType]:
            Generates and returns a dummy payload.
    """

    def _get_payload(self, *args, **kwargs) -> tuple[ImageStackDataType, ContextType]:
        """
        Generates and returns a dummy payload.

        The payload consists of:
        - `ImageStackDataType`: A 3D NumPy array with random data (a stack of 2D images).
        - `ContextType`: A dictionary containing dummy contextual information.

        Parameters:
            *args: Additional arguments for customization (not used in this implementation).
            **kwargs: Additional keyword arguments for customization (not used in this implementation).

        Returns:
            tuple[ImageStackDataType, dict]:
                A tuple containing the `ImageStackDataType` with dummy data and a
                `ContextType` dictionary with dummy metadata.
        """
        # Generate a dummy 3D NumPy array (stack of 10 images, each 256x256)
        dummy_stack = np.random.rand(10, 256, 256)  # Example stack of 10 images

        # Wrap the stack in an ImageStackDataType and return the payload
        return ImageStackDataType(dummy_stack), ContextType()
