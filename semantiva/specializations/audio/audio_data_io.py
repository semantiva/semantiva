from abc import abstractmethod
from semantiva.data_io import (
    PayloadSource,
    PayloadSink,
)
from semantiva.data_types import BaseDataType
from semantiva.context_operations.context_types import ContextType
from .audio_data_types import SingleChannelAudioDataType, DualChannelAudioDataType


class SingleChannelAudioSource(PayloadSource):
    """
    Abstract base class for single-channel audio data sources.

    This class defines methods to provide single-channel audio data.
    """

    @abstractmethod
    def _get_data(self):
        """
        Retrieve single-channel audio data.

        Returns:
            SingleChannelAudioDataType: The encapsulated audio data.
        """

    def get_data(self):
        """
        Fetch and return single-channel audio data.

        Returns:
            SingleChannelAudioDataType: The encapsulated audio data.
        """
        return self._get_data()


class DualChannelAudioSource(PayloadSource):
    """
    Abstract base class for dual-channel audio data sources.

    This class defines methods to provide dual-channel audio data.
    """

    @abstractmethod
    def _get_data(self):
        """
        Retrieve dual-channel audio data.

        Returns:
            DualChannelAudioDataType: The encapsulated audio data.
        """

    def get_data(self):
        """
        Fetch and return dual-channel audio data.

        Returns:
            DualChannelAudioDataType: The encapsulated audio data.
        """
        return self._get_data()


class SingleChannelAudioSink(PayloadSink):
    """
    Abstract base class for single-channel audio data sinks.

    This class defines methods to consume and store single-channel audio data.
    """

    @abstractmethod
    def _send_data(self, data: SingleChannelAudioDataType):
        """
        Consume single-channel audio data.

        Args:
            data (SingleChannelAudioDataType): The audio data to store.
        """

    def send_data(self, data: SingleChannelAudioDataType):
        """
        Consume and store single-channel audio data.

        Args:
            data (SingleChannelAudioDataType): The audio data to store.
        """
        self._send_data(data)


class DualChannelAudioSink(PayloadSink):
    """
    Abstract base class for dual-channel audio data sinks.

    This class defines methods to consume and store dual-channel audio data.
    """

    @abstractmethod
    def _send_data(self, data: DualChannelAudioDataType):
        """
        Consume dual-channel audio data.

        Args:
            data (DualChannelAudioDataType): The audio data to store.
        """

    def send_data(self, data: DualChannelAudioDataType):
        """
        Consume and store dual-channel audio data.

        Args:
            data (DualChannelAudioDataType): The audio data to store.
        """
        self._send_data(data)


class SingleChannelPayloadSource(PayloadSource):
    """
    Abstract base class for single-channel audio payload sources.

    This class defines methods to provide payloads containing single-channel audio data.
    """

    @abstractmethod
    def _get_payload(self):
        """
        Retrieve a payload of single-channel audio data.

        Returns:
            SingleChannelAudioDataType: The encapsulated audio data payload.
        """

    def get_payload(self):
        """
        Fetch and return a payload of single-channel audio data.

        Returns:
            SingleChannelAudioDataType: The encapsulated audio data payload.
        """
        return self._get_payload()


class DualChannelPayloadSource(PayloadSource):
    """
    Abstract base class for dual-channel audio payload sources.

    This class defines methods to provide payloads containing dual-channel audio data.
    """

    @abstractmethod
    def _get_payload(self):
        """
        Retrieve a payload of dual-channel audio data.

        Returns:
            DualChannelAudioDataType: The encapsulated audio data payload.
        """

    def get_payload(self):
        """
        Fetch and return a payload of dual-channel audio data.

        Returns:
            DualChannelAudioDataType: The encapsulated audio data payload.
        """
        return self._get_payload()


class SingleChannelPayloadSink(PayloadSink[SingleChannelAudioDataType]):
    """
    Abstract base class for single-channel audio payload sinks.

    This class defines methods to consume and store payloads containing single-channel audio data.
    """

    @abstractmethod
    def _send_payload(
        self, data: SingleChannelAudioDataType, context: ContextType, *args, **kwargs
    ):
        """
        Consume a payload of single-channel audio data.

        Args:
            payload (SingleChannelAudioDataType): The audio data payload to store.
        """

    def send_payload(
        self, data: SingleChannelAudioDataType, context: ContextType, *args, **kwargs
    ):
        """
        Consume and store a payload of single-channel audio data.

        Args:
            payload (SingleChannelAudioDataType): The audio data payload to store.
        """
        self._send_payload(data, context, *args, **kwargs)


class DualChannelPayloadSink(PayloadSink):
    """
    Abstract base class for dual-channel audio payload sinks.

    This class defines methods to consume and store payloads containing dual-channel audio data.
    """

    @abstractmethod
    def _send_payload(
        self, data: DualChannelAudioDataType, context: ContextType, *args, **kwargs
    ):
        """
        Consume a payload of dual-channel audio data.

        Args:
            payload (DualChannelAudioDataType): The audio data payload to store.
        """

    def send_payload(
        self, data: DualChannelAudioDataType, context: ContextType, *args, **kwargs
    ):
        """
        Consume and store a payload of dual-channel audio data.

        Args:
            payload (DualChannelAudioDataType): The audio data payload to store.
        """
        self._send_payload(data, context, *args, **kwargs)
