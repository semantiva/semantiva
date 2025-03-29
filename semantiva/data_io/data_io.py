from abc import abstractmethod
from typing import Tuple, TypeVar, Generic, List
from semantiva.context_processors import ContextType
from semantiva.data_types import BaseDataType
from semantiva.core import SemantivaObject

T = TypeVar("T", bound=BaseDataType)


class DataSource(SemantivaObject):
    """
    Abstract base class for data sources within the framework.

    A `DataSource` represents an entity that provides data to be consumed
    by other components in the framework.

    Methods:
        _get_data: Abstract method to implement the logic for retrieving data.
        get_data: Public method to fetch data by invoking `_get_data`.
        output_data_type: Abstract method to define the type of data provided.
    """

    @classmethod
    @abstractmethod
    def _get_data(cls, *args, **kwargs):
        """
        Abstract method to implement data retrieval logic.

        Args:
            *args: Positional arguments for data retrieval.
            **kwargs: Keyword arguments for data retrieval.

        Returns:
            Any: The retrieved data.
        """

    @classmethod
    def get_data(cls, *args, **kwargs):
        """
        Retrieve data by invoking the `_get_data` method.

        Args:
            *args: Positional arguments for data retrieval.
            **kwargs: Keyword arguments for data retrieval.

        Returns:
            Any: The retrieved data.
        """
        return cls._get_data(*args, **kwargs)

    @classmethod
    def _define_metadata(cls):

        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._get_data, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "DataSource",
            "output_data_type": cls.output_data_type().__name__,
            "input_parameters": annotated_parameter_list or "None",
        }

        return component_metadata

    @classmethod
    @abstractmethod
    def output_data_type(cls):
        """
        Define the type of data provided by this source.

        Returns:
            type: The data type provided by the source.
        """
        ...

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__name__}"


class PayloadSource(SemantivaObject):
    """
    Abstract base class for payload sources within the framework.

    A `PayloadSource` provides structured payloads for processing within
    the framework.

    Methods:
        _get_payload: Abstract method to implement the logic for retrieving payloads.
        get_payload: Public method to fetch payloads by invoking `_get_payload`.
        output_data_type: Abstract method to define the type of payload provided.
    """

    @classmethod
    def _define_metadata(cls):

        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._get_payload, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "PayloadSource",
            "output_data_type": cls.output_data_type().__name__,
            "input_parameters": annotated_parameter_list or "None",
            "injected_context_keys": cls.injected_context_keys() or "None",
        }

        return component_metadata

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

    @classmethod
    @abstractmethod
    def _injected_context_keys(self) -> List[str]:
        """
        Return the keys of the context that are injected by the source.

        Returns:
            List[str]: The keys of the context injected by the source.
        """

    @classmethod
    def injected_context_keys(cls) -> List[str]:
        """
        Return the keys of the context that are injected by the source.

        Returns:
            List[str]: The keys of the context injected by the source.
        """
        return cls._injected_context_keys()

    @classmethod
    @abstractmethod
    def output_data_type(cls) -> BaseDataType:
        """
        Define the type of payload provided by this source.

        Returns:
            BaseDataType: The data type provided by the source.
        """
        ...

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__name__}"


class DataSink(SemantivaObject, Generic[T]):
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

    @classmethod
    def _define_metadata(cls):

        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._send_data, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "DataSink",
            "input_data_type": cls.input_data_type().__name__,
            "input_parameters": annotated_parameter_list or "None",
        }

        return component_metadata

    def send_data(self, data: T, *args, **kwargs):
        """
        Send data by invoking the `_send_data` method.

        Args:
            *args: Positional arguments for data transmission.
            **kwargs: Keyword arguments for data transmission.

        Returns:
            None
        """
        return self._send_data(data, *args, **kwargs)

    @classmethod
    @abstractmethod
    def input_data_type(cls) -> BaseDataType[T]:
        """
        Define the type of data consumed by this sink.

        Returns:
            BaseDataType: The data type consumed by the sink.
        """

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__name__}"


class PayloadSink(SemantivaObject, Generic[T]):
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

    @classmethod
    def _define_metadata(cls):
        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._send_payload, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "PayloadSink",
            "input_data_type": cls.input_data_type().__name__,
            "input_parameters": annotated_parameter_list or "None",
        }

        return component_metadata

    @classmethod
    @abstractmethod
    def input_data_type(cls) -> BaseDataType[T]:
        """
        Define the type of data consumed by this sink.

        Returns:
            BaseDataType: The data type consumed by the sink.
        """

    @classmethod
    def __str__(cls) -> str:
        return f"{cls.__name__}"
