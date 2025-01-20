from abc import ABC, abstractmethod
from typing import Tuple, Type, TypeVar, Generic
from semantiva.context_operations import ContextType
from semantiva.data_types import BaseDataType

T = TypeVar("T", bound=BaseDataType)


class DataSource(ABC):
    """
    Abstract base class for data sources within the framework.

    A `DataSource` represents an entity that provides data to be consumed
    by other components in the framework.

    Methods:
        _get_data: Abstract method to implement the logic for retrieving data.
        get_data: Public method to fetch data by invoking `_get_data`.
        output_data_type: Abstract method to define the type of data provided.
    """

    @abstractmethod
    def _get_data(self, *args, **kwargs):
        """
        Abstract method to implement data retrieval logic.

        Args:
            *args: Positional arguments for data retrieval.
            **kwargs: Keyword arguments for data retrieval.

        Returns:
            Any: The retrieved data.
        """
        ...

    def get_data(self, *args, **kwargs):
        """
        Retrieve data by invoking the `_get_data` method.

        Args:
            *args: Positional arguments for data retrieval.
            **kwargs: Keyword arguments for data retrieval.

        Returns:
            Any: The retrieved data.
        """
        return self._get_data(*args, **kwargs)

    @abstractmethod
    def output_data_type(self):
        """
        Define the type of data provided by this source.

        Returns:
            type: The data type provided by the source.
        """
        ...


class PayloadSource(ABC):
    """
    Abstract base class for payload sources within the framework.

    A `PayloadSource` provides structured payloads for processing within
    the framework.

    Methods:
        _get_payload: Abstract method to implement the logic for retrieving payloads.
        get_payload: Public method to fetch payloads by invoking `_get_payload`.
        output_data_type: Abstract method to define the type of payload provided.
    """

    @abstractmethod
    def _get_payload(self, *args, **kwargs) -> Tuple[BaseDataType, ContextType]:
        """
        Abstract method to implement payload retrieval logic.

        Args:
            *args: Positional arguments for payload retrieval.
            **kwargs: Keyword arguments for payload retrieval.

        Returns:
            Tuple[BaseDataType, ContextType]: The retrieved payload and its context.
        """
        ...

    def get_payload(self, *args, **kwargs) -> Tuple[BaseDataType, ContextType]:
        """
        Retrieve a payload by invoking the `_get_payload` method.

        Args:
            *args: Positional arguments for payload retrieval.
            **kwargs: Keyword arguments for payload retrieval.

        Returns:
            Tuple[BaseDataType, ContextType]: The retrieved payload and its context
        """
        return self._get_payload(*args, **kwargs)

    @abstractmethod
    def output_data_type(self) -> BaseDataType:
        """
        Define the type of payload provided by this source.

        Returns:
            BaseDataType: The data type provided by the source.
        """
        ...


class DataSink(ABC, Generic[T]):
    """
    Abstract base class for data sinks within the framework.

    A `DataSink` represents an entity responsible for consuming and storing
    data provided by other components in the framework.

    Methods:
        _send_data: Abstract method to implement the logic for sending data.
        send_data: Public method to send data by invoking `_send_data`.
        input_data_type: Abstract method to define the type of data consumed.
    """

    @abstractmethod
    def _send_data(self, data: T, *args, **kwargs):
        """
        Abstract method to implement data transmission logic.

        Args:
            *args: Positional arguments for data transmission.
            **kwargs: Keyword arguments for data transmission.

        Returns:
            None
        """
        ...

    def send_data(self, data: T, *args, **kwargs):
        """
        Send data by invoking the `_send_data` method.

        Args:
            *args: Positional arguments for data transmission.
            **kwargs: Keyword arguments for data transmission.

        Returns:
            None
        """
        return self._send_data(*args, **kwargs)

    @abstractmethod
    def input_data_type(self) -> BaseDataType[T]:
        """
        Define the type of data consumed by this sink.

        Returns:
            BaseDataType: The data type consumed by the sink.
        """


class PayloadSink(ABC, Generic[T]):
    """
    Abstract base class for payload sinks within the framework.

    A `PayloadSink` represents an entity responsible for consuming and storing
    both data and its associated context provided by other components in the framework.

    Methods:
        _send_payload: Abstract method to implement the logic for consuming data and context.
        send_payload: Public method to consume data and context by invoking `_send_payload`.
    """

    @abstractmethod
    def _send_payload(self, data: T, context: ContextType, *args, **kwargs):
        """
        Abstract method to implement payload consumption logic.

        Args:
            data (BaseDataType): The data payload to consume.
            context (ContextType): The context associated with the data.
            *args: Additional positional arguments for payload consumption.
            **kwargs: Additional keyword arguments for payload consumption.

        Returns:
            None
        """
        pass

    def send_payload(self, data: T, context: ContextType, *args, **kwargs):
        """
        Consume the provided data and context by invoking the `_send_payload` method.

        Args:
            data (BaseDataType): The data payload to consume.
            context (ContextType): The context associated with the data.
            *args: Additional positional arguments for payload consumption.
            **kwargs: Additional keyword arguments for payload consumption.

        Returns:
            None
        """
        self._send_payload(data, context, *args, **kwargs)

    @abstractmethod
    def input_data_type(self) -> BaseDataType[T]:
        """
        Define the type of data consumed by this sink.

        Returns:
            BaseDataType: The data type consumed by the sink.
        """
