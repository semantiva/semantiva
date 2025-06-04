# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import abstractmethod
from typing import Dict, Any, Tuple, TypeVar, Generic, List
from semantiva.context_processors import ContextType
from semantiva.data_types import BaseDataType
from semantiva.core import SemantivaObject

T = TypeVar("T", bound=BaseDataType)


class DataSource(SemantivaObject):
    """Abstract base class representing a data source in Semantiva."""

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
    def _define_metadata(cls) -> Dict[str, Any]:

        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._get_data, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "DataSource",
            "input_parameters": annotated_parameter_list or "None",
        }

        try:
            component_metadata["output_data_type"] = cls.output_data_type().__name__
        except Exception:
            # no binding available at this abstract level
            pass

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
    """Abstract base class for providing structured payloads (data and context) in Semantiva."""

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:

        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._get_payload, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "PayloadSource",
            "input_parameters": annotated_parameter_list,
            "injected_context_keys": cls.injected_context_keys(),
        }

        try:
            output_type = cls.output_data_type()
            component_metadata["output_data_type"] = getattr(
                output_type, "__name__", str(output_type)
            )
        except Exception:
            # no binding available at this abstract level
            pass

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
    """Abstract base class for data sinks that consume and store data."""

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
    def _define_metadata(cls) -> Dict[str, Any]:

        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._send_data, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "DataSink",
            "input_parameters": annotated_parameter_list or "None",
        }

        try:
            input_type = cls.input_data_type()
            component_metadata["input_data_type"] = getattr(
                input_type, "__name__", str(input_type)
            )
        except Exception:
            # no binding available at this abstract level
            pass

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
    """Abstract base class for payload sinks that consume and store data along with its associated context."""

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
    def _define_metadata(cls) -> Dict[str, Any]:
        excluded_parameters = ["self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._send_payload, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "PayloadSink",
            "input_parameters": annotated_parameter_list or "None",
        }

        try:
            input_type = cls.input_data_type()
            component_metadata["input_data_type"] = getattr(
                input_type, "__name__", str(input_type)
            )
        except Exception:
            # no binding available at this abstract level
            pass

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
