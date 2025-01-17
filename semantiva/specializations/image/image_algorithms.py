import numpy as np
from .image_data_types import ImageDataType, ImageStackDataType
from .image_operations import ImageAlgorithm, ImageStackToImageProjector


class ImageSubtraction(ImageAlgorithm):
    """
    A class for performing image subtraction.

    This class inherits from `ImageAlgorithm` and implements an operation
    to subtract one image from another. Both images must be instances of
    `ImageDataType`, ensuring that they are 2D NumPy arrays.

    Methods:
        _operation(data: ImageDataType, subtracting_image: ImageDataType) -> ImageDataType:
            Performs the subtraction operation between the input image and the subtracting image.
    """

    def _operation(
        self, data: ImageDataType, image_to_subtract: ImageDataType
    ) -> ImageDataType:
        """
        Subtracts one image from another.

        Parameters:
            data (ImageDataType): The original image data.
            image_to_subtract (ImageDataType): The image data to subtract.

        Returns:
            ImageDataType: The result of the subtraction operation.
        """
        return ImageDataType(np.subtract(data.data, image_to_subtract.data))


class ImageAddition(ImageAlgorithm):
    """
    A class for performing image addition.

    This class inherits from `ImageAlgorithm` and implements an operation
    to add one image to another. Both images must be instances of
    `ImageDataType`, ensuring that they are 2D NumPy arrays.

    Methods:
        _operation(data: ImageDataType, added_image: ImageDataType) -> ImageDataType:
            Performs the addition operation between the input image and the added image.
    """

    def _operation(
        self, data: ImageDataType, image_to_add: ImageDataType
    ) -> ImageDataType:
        """
        Adds one image to another.

        Parameters:
            data (ImageDataType): The original image data.
            image_to_add (ImageDataType): The image data to add.

        Returns:
            ImageDataType: The result of the addition operation.
        """
        return ImageDataType(np.add(data.data, image_to_add.data))


class ImageClipping(ImageAlgorithm):
    """
    A class for clipping a region from an image.

    This class inherits from `ImageAlgorithm` and implements an operation
    to clip a rectangular region from the input image.
    """

    def _operation(
        self,
        data: ImageDataType,
        x_start: int,
        x_end: int,
        y_start: int,
        y_end: int,
    ) -> ImageDataType:
        """
        Clips a rectangular region from the input image.

        Parameters:
            data (ImageDataType): The original image data.
            x_start (int): The starting x-coordinate of the clipping region.
            x_end (int): The ending x-coordinate of the clipping region.
            y_start (int): The starting y-coordinate of the clipping region.
            y_end (int): The ending y-coordinate of the clipping region.

        Returns:
            ImageDataType: The clipped region of the image.

        Raises:
            ValueError: If the specified clipping region is out of bounds.
        """

        # Ensure the region is within bounds
        if not 0 <= x_start < x_end <= data.data.shape[1]:
            raise ValueError(
                f"x-coordinates out of bounds: x_start={x_start}, x_end={x_end}, width={data.data.shape[1]}"
            )
        if not 0 <= y_start < y_end <= data.data.shape[0]:
            raise ValueError(
                f"y-coordinates out of bounds: y_start={y_start}, y_end={y_end}, height={data.data.shape[0]}"
            )

        clipped_data = data.data[y_start:y_end, x_start:x_end]
        return ImageDataType(clipped_data)


class StackToImageMeanProjector(ImageStackToImageProjector):
    """
    A concrete implementation of ImageStackFlattener that projects a stack of images
    into a single image by taking the mean along the slices.
    """

    def _operation(self, data: ImageStackDataType):
        """
        Computes the mean projection of an image stack.

        Parameters:
            data (ImageStackDataType): The input image stack, represented as a 3D NumPy array
                                        (stack of 2D images).

        Returns:
            ImageDataType: A single 2D image resulting from the mean projection of the stack.

        Raises:
            ValueError: If the input data is not a 3D NumPy array.

        """
        # Compute the mean along the stack (first axis)
        return ImageDataType(np.mean(data.data, axis=0))
