from semantiva.data_processors import DataOperation, DataProbe
from .audio_data_types import SingleChannelAudioDataType, DualChannelAudioDataType


class SingleChannelAudioOperation(DataOperation):
    """
    An operation specialized for processing single-channel audio data.

    This class implements the `DataOperation` abstract base class to define
    operations that accept and produce `SingleChannelAudioDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @staticmethod
    def input_data_type():
        """
        Specify the input data type for the operation.

        Returns:
            type: `SingleChannelAudioDataType`, representing single-channel audio.
        """
        return SingleChannelAudioDataType

    @staticmethod
    def output_data_type():
        """
        Specify the output data type for the operation.

        Returns:
            type: `SingleChannelAudioDataType`, representing single-channel audio.
        """
        return SingleChannelAudioDataType


class DualChannelAudioOperation(DataOperation):
    """
    An operation specialized for processing dual-channel (stereo) audio data.

    This class implements the `DataOperation` abstract base class to define
    operations that accept and produce `DualChannelAudioDataType`.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @staticmethod
    def input_data_type():
        """
        Specify the input data type for the operation.

        Returns:
            type: `DualChannelAudioDataType`, representing dual-channel audio.
        """
        return DualChannelAudioDataType

    @staticmethod
    def output_data_type():
        """
        Specify the output data type for the operation.

        Returns:
            type: `DualChannelAudioDataType`, representing dual-channel audio.
        """
        return DualChannelAudioDataType


class DualChannelMergerOperation(DataOperation):
    """
    An operation to merge dual-channel audio data into a single-channel format.

    This class defines operations that accept `DualChannelAudioDataType` as input
    and produce `SingleChannelAudioDataType` as output, suitable for scenarios
    where stereo audio needs to be downmixed.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @staticmethod
    def input_data_type():
        """
        Specify the input data type for the operation.

        Returns:
            type: `DualChannelAudioDataType`, representing dual-channel audio.
        """
        return DualChannelAudioDataType

    @staticmethod
    def output_data_type():
        """
        Specify the output data type for the operation.

        Returns:
            type: `SingleChannelAudioDataType`, representing single-channel audio.
        """
        return SingleChannelAudioDataType


class SingleChannelExpanderOperation(DataOperation):
    """
    An operation to expand single-channel audio data into dual-channel format.

    This class defines operations that accept `SingleChannelAudioDataType` as input
    and produce `DualChannelAudioDataType` as output, suitable for scenarios
    where mono audio needs to be converted to stereo.

    Methods:
        input_data_type: Returns the expected input data type.
        output_data_type: Returns the type of data output by the operation.
    """

    @staticmethod
    def input_data_type():
        """
        Specify the input data type for the operation.

        Returns:
            type: `SingleChannelAudioDataType`, representing single-channel audio.
        """
        return SingleChannelAudioDataType

    @staticmethod
    def output_data_type():
        """
        Specify the output data type for the operation.

        Returns:
            type: `DualChannelAudioDataType`, representing dual-channel audio.
        """
        return DualChannelAudioDataType


class SingleChannelAudioProbe(DataProbe):
    """
    A probe for inspecting or monitoring single-channel audio data.

    This class implements the `DataProbe` abstract base class to define
    operations that accept `SingleChannelAudioDataType` as input. It is
    typically used for debugging, logging, or analyzing single-channel
    audio data within the framework.

    Methods:
        input_data_type: Returns the expected input data type for the probe.
    """

    @staticmethod
    def input_data_type():
        """
        Specify the input data type for the probe.

        Returns:
            type: `SingleChannelAudioDataType`, representing single-channel audio.
        """
        return SingleChannelAudioDataType


class DualChannelAudioProbe(DataProbe):
    """
    A probe for inspecting or monitoring dual-channel (stereo) audio data.

    This class implements the `DataProbe` abstract base class to define
    operations that accept `DualChannelAudioDataType` as input. It is
    typically used for debugging, logging, or analyzing dual-channel
    audio data within the framework.

    Methods:
        input_data_type: Returns the expected input data type for the probe.
    """

    @staticmethod
    def input_data_type():
        """
        Specify the input data type for the probe.

        Returns:
            type: `DualChannelAudioDataType`, representing dual-channel audio.
        """
        return DualChannelAudioDataType
