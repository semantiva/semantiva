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

import inspect
from typing import Type, List
from semantiva.data_io import DataSource, PayloadSource, DataSink, PayloadSink
from semantiva.data_processors.data_processors import DataOperation
from semantiva.data_types import BaseDataType, NoDataType
from semantiva.pipeline.payload import Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.logger import Logger
from semantiva.data_processors.data_processors import ParameterInfo, _NO_DEFAULT
from collections import OrderedDict


class _IOOperationFactory:
    """
    A factory class for wrapping data IO classes into data processors.

    This class provides a method for creating a data processor instance based on the provided class name.
    """

    @classmethod
    def create_data_operation(
        cls,
        data_io_class: (
            Type[DataSource] | Type[PayloadSource] | Type[DataSink] | Type[PayloadSink]
        ),
    ) -> Type[DataOperation]:
        """
        Dynamically create a :class:`DataOperation` subclass that wraps a data-IO class.

        Args:
            cls: Factory class reference.
            data_io_class: The ``DataSource``/``PayloadSource``/``DataSink``/``PayloadSink``
                class to wrap.

        Returns:
            Type[DataOperation]: A new subclass of ``DataOperation`` with matching I/O types.
        """

        methods: dict = {}

        if issubclass(data_io_class, (DataSource, PayloadSource)):

            def get_no_data_type():
                """Return ``NoDataType``."""
                return NoDataType

            def input_data_type_method(cls) -> BaseDataType:
                """Return NoDataType: data sources do not accept input data."""
                return get_no_data_type()

            def output_data_type_method(cls) -> BaseDataType:
                """Return the data type produced by the underlying source."""
                return data_io_class.output_data_type()

            if issubclass(data_io_class, DataSource):

                def _process_logic_method(
                    self, data: BaseDataType, *args, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    loaded_data = data_io_instance.get_data(*args, **kwargs)
                    return loaded_data

                def get_processing_parameter_names(cls) -> List[str]:
                    """
                    Retrieve the names of parameters required by the `_get_data` method.

                    Returns:
                        List[str]: A list of parameter names (excluding `self` and `data`).
                    """
                    signature = inspect.signature(data_io_class._get_data)
                    return [
                        param.name
                        for param in signature.parameters.values()
                        if param.name not in {"self", "data"}
                        and param.kind
                        not in {
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        }
                    ]

            elif issubclass(data_io_class, PayloadSource):

                def _process_logic_method(
                    self, data: BaseDataType, *args, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    payload = data_io_instance._get_payload(*args, **kwargs)
                    loaded_data = payload.data
                    # If the payload provides a context, notify the DataOperation observer
                    loaded_context = payload.context

                    for key, value in loaded_context.items():
                        self._notify_context_update(key, value)

                    # Return only the loaded data (context is injected via notifications)
                    return loaded_data

                def get_processing_parameter_names(cls) -> List[str]:
                    """
                    Retrieve the names of parameters required by the `_get_payload` method.

                    Returns:
                        List[str]: A list of parameter names (excluding `self` and `data`).
                    """
                    signature = inspect.signature(data_io_class._get_payload)
                    return [
                        param.name
                        for param in signature.parameters.values()
                        if param.name not in {"self", "data"}
                        and param.kind
                        not in {
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        }
                    ]

                def context_keys_method(cls) -> list:
                    """Return context keys injected by the payload source."""
                    return list(data_io_class.injected_context_keys())

                def get_created_keys_method(cls) -> list:
                    """Return context keys created by this operation."""
                    return cls.context_keys()

                # expose created/context keys so the node metadata and notifications work
                methods["context_keys"] = classmethod(context_keys_method)
                methods["get_created_keys"] = classmethod(get_created_keys_method)

        elif issubclass(data_io_class, (DataSink, PayloadSink)):

            def input_data_type_method(cls) -> BaseDataType:
                """Return the data type consumed by the underlying sink."""
                return data_io_class.input_data_type()

            def output_data_type_method(cls) -> BaseDataType:
                """Return the data type passed through by the sink."""
                return data_io_class.input_data_type()

            if issubclass(data_io_class, DataSink):

                def _process_logic_method(
                    self, data: BaseDataType, *args, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    data_io_instance.send_data(data, *args, **kwargs)
                    return data

                def get_processing_parameter_names(cls) -> List[str]:
                    """
                    Retrieve the names of parameters required by the `_send_data` method.

                    Returns:
                        List[str]: A list of parameter names (excluding `self` and `data`).
                    """

                    signature = inspect.signature(data_io_class._send_data)
                    return [
                        param.name
                        for param in signature.parameters.values()
                        if param.name not in {"self", "data"}
                        and param.kind
                        not in {
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        }
                    ]

            elif issubclass(data_io_class, PayloadSink):

                def _process_logic_method(
                    self, data: BaseDataType, *args, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    data_io_instance._send_payload(
                        Payload(data, ContextType()), *args, **kwargs
                    )
                    Logger().warning(
                        f"Context sending from Wrapped PayloadSink in pipelines is not supported ({data_io_class.__name__})"
                    )
                    return data

                def get_processing_parameter_names(cls) -> List[str]:
                    """
                    Retrieve the names of parameters required by the `_send_payload` method.

                    Returns:
                        List[str]: A list of parameter names (excluding `self` and `payload`).
                    """

                    signature = inspect.signature(data_io_class._send_payload)
                    return [
                        param.name
                        for param in signature.parameters.values()
                        if param.name not in {"self", "payload"}
                        and param.kind
                        not in {
                            inspect.Parameter.VAR_POSITIONAL,
                            inspect.Parameter.VAR_KEYWORD,
                        }
                    ]

        else:
            raise ValueError(f"Invalid data IO class: {data_io_class}.")

        methods["_process_logic"] = _process_logic_method
        methods["input_data_type"] = classmethod(input_data_type_method)
        methods["output_data_type"] = classmethod(output_data_type_method)
        methods["get_processing_parameter_names"] = classmethod(
            get_processing_parameter_names
        )

        # Build parameter metadata from the underlying data-IO method signature
        try:
            sig = inspect.signature(
                # choose the correct method to inspect
                data_io_class._get_data
                if issubclass(data_io_class, DataSource)
                else (
                    data_io_class._get_payload
                    if issubclass(data_io_class, PayloadSource)
                    else (
                        data_io_class._send_data
                        if issubclass(data_io_class, DataSink)
                        else data_io_class._send_payload
                    )
                )
            )
        except Exception:
            sig = None

        if sig:
            details = OrderedDict()
            for param in sig.parameters.values():
                if param.name in {"self", "data", "payload"}:
                    continue
                if param.kind in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }:
                    continue
                default = (
                    param.default
                    if param.default is not inspect._empty
                    else _NO_DEFAULT
                )
                annotation = (
                    getattr(param.annotation, "__name__", str(param.annotation))
                    if param.annotation is not inspect._empty
                    else "Unknown"
                )
                details[param.name] = ParameterInfo(
                    default=default, annotation=annotation
                )

            def _define_metadata_override(cls):
                # Start from DataOperation metadata and inject our parameter details
                # Use super() to invoke the parent class implementation bound to `cls`
                base = super(DataOperation, cls)._define_metadata()
                base["parameters"] = details
                return base

            methods["_define_metadata"] = classmethod(_define_metadata_override)

        # Create a new type that extends DataOperation
        class_name = f"{data_io_class.__name__}"
        generated_class = type(class_name, (DataOperation,), methods)
        # Propagate the wrapped class docstring for introspection tools
        generated_class.__doc__ = getattr(data_io_class, "__doc__", None)
        assert issubclass(generated_class, DataOperation)
        return generated_class
