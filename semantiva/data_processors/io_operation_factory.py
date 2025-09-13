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

"""
IO Operation Factory (role-preserving adapter)

This module builds *adapters* that wrap DataSource/PayloadSource and
DataSink/PayloadSink classes into lightweight DataOperation subclasses so the
pipeline engine can drive any component via a single `_process_logic` interface.

Key points:
  • This is an adapter, not a role change. The canonical class remains a source
    or sink. The wrapper only exists at the node execution boundary.
  • Source wrappers:
      - input_data_type() -> NoDataType
      - output_data_type() -> underlying DataSource.output_data_type()
      - `_process_logic(...)` forwards context (if the source accepts it) and
        calls the source's public `get_data(...)` API.
      - Parameter metadata is mirrored from the source's `_get_data` signature.
      - If the source advertises `get_context_requirements()` or `get_created_keys()`,
        the wrapper forwards them so inspection remains accurate.
  • PayloadSource wrappers: similar, but they call `_get_payload(...)` and inject
    payload.context into the node observer via `_notify_context_update(...)`.
  • Sink wrappers:
      - input_data_type() -> sink.input_data_type()
      - output_data_type() -> sink.input_data_type() (pass-through)
      - `_process_logic(data, ...)` calls the sink's send method and returns `data`.
      - PayloadSink wrappers build a `Payload(data, ContextType())` and warn that
        context send is not supported inside pipeline execution.

This factory exists solely to unify node execution; it does not alter framework
ontology. See `_pipeline_node_factory.py` for how/when adapters are applied.
"""

import inspect
from typing import Any, Type, List, cast
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
    Build role-preserving DataOperation adapters for IO components.

    Given a DataSource/PayloadSource or DataSink/PayloadSink class, produce a
    thin DataOperation subclass that mirrors the underlying method signature
    and context behavior. Adapters are used by the pipeline node factory to
    standardize execution without changing the component's canonical role.

    The adapter pattern ensures:
    - Sources remain sources (NoDataType input, produce output)
    - Sinks remain sinks (consume input, pass-through output)
    - Parameter signatures are preserved exactly for inspection
    - Context forwarding works correctly (FromContext parameters, etc.)
    - Metadata (created keys, requirements) flows through accurately

    This factory exists solely for execution uniformity, not ontological change.
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

        # Container for dynamically-created methods that will be attached
        # to the generated DataOperation subclass. We populate this dict
        # as we inspect the wrapped data-IO class and then construct
        # the runtime class via `type(...)` at the end of the function.
        methods: dict = {}

        # Branch depending on the kind of data-IO we were given. Sources
        # (DataSource, PayloadSource) produce data; sinks consume it. We
        # generate different wrapper logic for each case so pipelines can
        # treat both uniformly as DataOperation instances.
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

                # For DataSource subclasses we mirror the `_get_data`
                # signature on the generated `_process_logic` method so
                # introspection and parameter wiring remain exact. This
                # makes the wrapper transparent to the rest of the system.
                source_sig = inspect.signature(data_io_class._get_data)
                source_params = [
                    p for name, p in source_sig.parameters.items() if name != "self"
                ]
                # Detect whether the underlying source accepts a `context`
                # parameter (or **kwargs). If so, we will forward the
                # pipeline observer context when calling the data-IO.
                accepts_context = "context" in source_sig.parameters or any(
                    p.kind is inspect.Parameter.VAR_KEYWORD
                    for p in source_sig.parameters.values()
                )

                # Create parameter list for the new method
                new_params = [
                    inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                    inspect.Parameter(
                        "data",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=BaseDataType,
                    ),
                ] + source_params

                new_sig = inspect.Signature(
                    parameters=new_params, return_annotation=BaseDataType
                )

                # The wrapper method created here will call the underlying
                # data-IO's public API. When the wrapped call expects a
                # `context` we populate it from the node's bound
                # `context_observer` so FromContext-style parameters work at
                # runtime. We intentionally accept **kwargs to preserve the
                # original call signature shape (the precise signature is
                # attached below via __signature__ for introspection).
                def _process_logic_method(
                    self, data: BaseDataType, **kwargs
                ) -> BaseDataType:
                    if accepts_context and self.context_observer is not None:
                        # Provide the pipeline observer context to the call. This preserves
                        # FromContext-style semantics with no role change: the source still
                        # behaves as a source, but can access pipeline context when needed.
                        kwargs.setdefault(
                            "context", self.context_observer.observer_context
                        )
                    data_io_instance = data_io_class()
                    loaded_data = data_io_instance.get_data(**kwargs)
                    return loaded_data

                # Apply the exact signature so tools like inspection and
                # parameter resolution see the same parameters as the
                # original `_get_data` method. This does not change the
                # runtime call semantics (we still accept **kwargs above).
                setattr(_process_logic_method, "__signature__", new_sig)

                # Expose a `get_processing_parameter_names` classmethod
                # on the generated wrapper. Prefer the underlying class's
                # own implementation if available; otherwise derive the
                # parameter list from the inspected signature.
                if hasattr(data_io_class, "get_processing_parameter_names"):

                    def get_processing_parameter_names(cls) -> List[str]:
                        return list(
                            cast(Any, data_io_class).get_processing_parameter_names()
                        )

                else:

                    def get_processing_parameter_names(cls) -> List[str]:
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

                # Provide a `get_context_requirements` shim. Many data-IO
                # classes expose the parameters they need; if not, fall
                # back to the same logic used above.
                if hasattr(data_io_class, "get_context_requirements"):

                    def get_context_requirements(cls) -> List[str]:
                        return list(cast(Any, data_io_class).get_context_requirements())

                else:

                    def get_context_requirements(cls) -> List[str]:
                        try:
                            return list(
                                cast(
                                    Any, data_io_class
                                ).get_processing_parameter_names()
                            )
                        except AttributeError:
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

                # If the underlying data-IO advertises created context keys
                # expose them from the wrapper as well so node metadata can
                # report what this operation will inject into the pipeline
                # context at runtime.
                if hasattr(data_io_class, "get_created_keys"):

                    def get_created_keys_method(cls) -> list:
                        return list(cast(Any, data_io_class).get_created_keys())

                else:

                    def get_created_keys_method(cls) -> list:
                        return []

                methods["get_context_requirements"] = classmethod(
                    get_context_requirements
                )
                methods["get_created_keys"] = classmethod(get_created_keys_method)

            elif issubclass(data_io_class, PayloadSource):

                # Generate _process_logic with exact signature from _get_payload
                source_sig = inspect.signature(data_io_class._get_payload)
                source_params = [
                    p for name, p in source_sig.parameters.items() if name != "self"
                ]

                # Create parameter list for the new method
                new_params = [
                    inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                    inspect.Parameter(
                        "data",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=BaseDataType,
                    ),
                ] + source_params

                new_sig = inspect.Signature(
                    parameters=new_params, return_annotation=BaseDataType
                )

                # PayloadSource: the wrapped call returns a Payload object that
                # may include additional context to be injected into the
                # pipeline. We propagate those values via the operation's
                # `_notify_context_update` hook so downstream nodes can use
                # them.
                def _process_logic_method(
                    self, data: BaseDataType, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    payload = data_io_instance._get_payload(**kwargs)
                    loaded_data = payload.data
                    # If the payload provides a context, notify the DataOperation observer
                    loaded_context = payload.context

                    for key, value in loaded_context.items():
                        self._notify_context_update(key, value)

                    # Return only the loaded data (context is injected via notifications)
                    return loaded_data

                # Apply the exact signature
                setattr(_process_logic_method, "__signature__", new_sig)

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

                # Helper exposing context keys that the payload source will
                # inject. This is used by node metadata consumers.
                def context_keys_method(cls) -> list:
                    """Return context keys injected by the payload source."""
                    return list(data_io_class.injected_context_keys())

                def get_created_keys_method(cls) -> list:
                    """Return context keys created by this operation."""
                    return cls.context_keys()

                # expose created/context keys so the node metadata and notifications work
                methods["context_keys"] = classmethod(context_keys_method)
                methods["get_created_keys"] = classmethod(get_created_keys_method)

        # Sinks are consumers: wrap their send methods similarly but note
        # that they will not create new pipeline data (they may still
        # expose parameters for configuration).
        elif issubclass(data_io_class, (DataSink, PayloadSink)):

            def input_data_type_method(cls) -> BaseDataType:
                """Return the data type consumed by the underlying sink."""
                return data_io_class.input_data_type()

            def output_data_type_method(cls) -> BaseDataType:
                """Return the data type passed through by the sink."""
                return data_io_class.input_data_type()

            if issubclass(data_io_class, DataSink):

                # Generate _process_logic with exact signature from _send_data
                source_sig = inspect.signature(data_io_class._send_data)
                source_params = [
                    p
                    for name, p in source_sig.parameters.items()
                    if name not in {"self", "data"}
                ]

                # Create parameter list for the new method
                new_params = [
                    inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                    inspect.Parameter(
                        "data",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=BaseDataType,
                    ),
                ] + source_params

                new_sig = inspect.Signature(
                    parameters=new_params, return_annotation=BaseDataType
                )

                def _process_logic_method(
                    self, data: BaseDataType, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    data_io_instance.send_data(data, **kwargs)
                    return data

                # Apply the exact signature
                setattr(_process_logic_method, "__signature__", new_sig)

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

                # Generate _process_logic with exact signature from _send_payload
                source_sig = inspect.signature(data_io_class._send_payload)
                source_params = [
                    p
                    for name, p in source_sig.parameters.items()
                    if name not in {"self", "payload"}
                ]

                # Create parameter list for the new method
                new_params = [
                    inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                    inspect.Parameter(
                        "data",
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=BaseDataType,
                    ),
                ] + source_params

                new_sig = inspect.Signature(
                    parameters=new_params, return_annotation=BaseDataType
                )

                def _process_logic_method(
                    self, data: BaseDataType, **kwargs
                ) -> BaseDataType:
                    data_io_instance = data_io_class()
                    data_io_instance._send_payload(
                        Payload(data, ContextType()), **kwargs
                    )
                    Logger().warning(
                        f"Context sending from Wrapped PayloadSink in pipelines is not supported ({data_io_class.__name__})"
                    )
                    return data

                # Apply the exact signature
                setattr(_process_logic_method, "__signature__", new_sig)

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

        # Build a ParameterInfo map from the inspected signature so the
        # runtime metadata for the generated class contains accurate
        # parameter defaults and annotations. This drives CLI UX and
        # automated parameter validation.
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

        # Create a new subclass of DataOperation with the constructed
        # methods and metadata. This generated class behaves like a
        # thin adapter around the original data-IO class but integrates
        # with the pipeline's inspection and context systems.
        class_name = f"{data_io_class.__name__}"
        generated_class = type(class_name, (DataOperation,), methods)
        # Propagate the wrapped class docstring for introspection tools
        generated_class.__doc__ = getattr(data_io_class, "__doc__", None)
        assert issubclass(generated_class, DataOperation)
        return generated_class
