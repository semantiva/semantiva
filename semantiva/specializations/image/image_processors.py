from semantiva.data_processors import DataOperation, DataProbe
from .image_data_types import ImageDataType, ImageStackDataType


class ImageOperation(DataOperation):
    """
    An operation specialized for processing ImageDataType data.

    This class implements the `DataOperation` abstract base class to define
    operations that accept and produce `ImageDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the operation.

        Returns:
            type: `ImageDataType`, representing Image.
        """
        return ImageDataType

    @classmethod
    def output_data_type(cls):
        """
        Specify the output data type for the operation.

        Returns:
            type: `ImageDataType`, representing Image.
        """
        return ImageDataType


class ImageStackAlgorithm(DataOperation):
    """
    An operation specialized for processing ImageStackDataType data.

    This class implements the `DataOperation` abstract base class to define
    operations that accept and produce `ImageStackDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the operation.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType

    @classmethod
    def output_data_type(cls):
        """
        Specify the output data type for the operation.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType


class ImageStackToImageProjector(DataOperation):
    """
    An operation specialized for flattening ImageStackDataType data.

    This class implements the `DataOperation` abstract base class to define
    operations that accept `ImageStackDataType` and produce `ImageDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the operation.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType

    @classmethod
    def output_data_type(cls):
        """
        Specify the output data type for the operation.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageDataType


class ImageProbe(DataProbe):
    """
    A probe for inspecting or monitoring ImageDataType data.

    This class implements the `DataProbe` abstract base class to define
    operations that accept and produce `ImageDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the operation.

        Returns:
            type: `ImageDataType`, representing Image.
        """
        return ImageDataType


class ImageStackProbe(DataProbe):
    """
    A probe for inspecting or monitoring ImageStackDataType data.

    This class implements the `DataProbe` abstract base class to define
    operations that accept and produce `ImageStackDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
    """

    @classmethod
    def input_data_type(cls):
        """
        Specify the input data type for the operation.

        Returns:
            type: `ImageStackDataType`, representing a stack of images.
        """
        return ImageStackDataType
