from semantiva.data_operations import DataAlgorithm
from .image_data_types import ImageDataType, ImageStackDataType


class ImageAlgorithm(DataAlgorithm):
    """
    An algorithm specialized for processing ImageDataType data.

    This class implements the `DataAlgorithm` abstract base class to define
    operations that accept and produce `ImageDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the algorithm.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the algorithm.

        Returns:
            type: `ImageDataType`, representing Image.
        """
        return ImageDataType

    @classmethod
    def output_data_type(cls):
        """
        Specify the output data type for the algorithm.

        Returns:
            type: `ImageDataType`, representing Image.
        """
        return ImageDataType


class ImageStackAlgorithm(DataAlgorithm):
    """
    An algorithm specialized for processing ImageStackDataType data.

    This class implements the `DataAlgorithm` abstract base class to define
    operations that accept and produce `ImageStackDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the algorithm.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the algorithm.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType

    @classmethod
    def output_data_type(cls):
        """
        Specify the output data type for the algorithm.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType


class ImageStackToImageProjector(DataAlgorithm):
    """
    An algorithm specialized for flattening ImageStackDataType data.

    This class implements the `DataAlgorithm` abstract base class to define
    operations that accept `ImageStackDataType` and produce `ImageDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the algorithm.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the algorithm.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType

    @classmethod
    def output_data_type(cls):
        """
        Specify the output data type for the algorithm.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageDataType
