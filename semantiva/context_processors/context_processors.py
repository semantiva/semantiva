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
import inspect
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Callable

from semantiva.data_processors.data_processors import ParameterInfo, _NO_DEFAULT
from semantiva.context_processors.context_types import ContextType
from semantiva.context_processors.context_observer import _ContextObserver
from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.data_types.data_types import BaseDataType
from semantiva.logger import Logger


class ContextProcessor(_SemantivaComponent):
    """Base class for performing context operations.

    Subclasses implement :meth:`_process_logic` as a **pure function** that accepts
    only runtime parameters. Any modifications to the active context must be
    mediated through :meth:`_notify_context_update` which delegates writes to the
    provided :class:`~semantiva.context_processors.context_observer._ContextObserver`.
    """

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)

    # --- ContextObserver lifecycle (set by node) ---
    _context_observer: Optional[_ContextObserver] = None

    def _set_context_observer(self, observer: Optional[_ContextObserver]) -> None:
        self._context_observer = observer

    def _notify_context_update(self, key: str, value: Any) -> None:
        """Safely update the active context via the observer."""
        if self._context_observer is None:
            raise RuntimeError(
                f"{self.__class__.__name__} attempted a context update without an active ContextObserver."
            )
        self._context_observer.update(key, value)

    def _notify_context_deletion(self, key: str) -> None:
        """Safely delete a key from the active context via the observer."""
        if self._context_observer is None:
            raise RuntimeError(
                f"{self.__class__.__name__} attempted a context deletion without an active ContextObserver."
            )
        self._context_observer.delete(key)

    def operate_context(
        self,
        *,
        context: ContextType,
        context_observer: Optional[_ContextObserver],
        **kwargs,
    ) -> ContextType:
        """Execute the context operation.

        Parameters are resolved externally and provided as ``kwargs``. The context
        is only accessible through ``_notify_context_update`` via the context observer.
        Direct context access is not supported - all context interactions must be
        mediated through the observer pattern.
        """
        self.logger.debug(
            f"Executing {self.__class__.__name__} with params={list(kwargs.keys())}"
        )
        self._set_context_observer(context_observer)
        try:
            self._process_logic(**kwargs)
        finally:
            self._set_context_observer(None)
        return context

    @abstractmethod
    def _process_logic(self, *args, **kwargs) -> None:
        """Implement stateless logic using only runtime parameters.

        All context interactions must be done through _notify_context_update().
        Direct context parameter access is not supported.

        Args:
            *args, **kwargs: Runtime parameters resolved from pipeline configuration and context.
                           Implementations should declare specific parameters instead of using
                           *args, **kwargs for reliable provenance tracking. The base signature
                           uses *args, **kwargs only for type compatibility.
        """

    @classmethod
    def input_data_type(cls):
        """Return the placeholder data type accepted by context processors."""
        return BaseDataType

    # ===== Introspection API =====
    @classmethod
    def get_processing_parameter_names(cls) -> List[str]:
        """Names of ``_process_logic`` parameters excluding ``self``."""
        sig = inspect.signature(cls._process_logic)
        names: List[str] = []
        for p in sig.parameters.values():
            if p.name == "self":
                continue
            if p.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }:
                continue
            names.append(p.name)
        return names

    @classmethod
    def _retrieve_parameter_details(
        cls, class_attribute: Callable, excluded: List[str]
    ) -> "OrderedDict[str, ParameterInfo]":
        signatures = cls._retrieve_parameter_signatures(class_attribute, excluded)
        sig_map = {name: annotation for name, annotation in signatures}
        sig = inspect.signature(class_attribute)
        details: "OrderedDict[str, ParameterInfo]" = OrderedDict()
        for p in sig.parameters.values():
            if p.name in excluded or p.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }:
                continue
            default = p.default if p.default is not inspect._empty else _NO_DEFAULT
            annotation = sig_map.get(p.name, "Unknown")
            details[p.name] = ParameterInfo(default=default, annotation=annotation)
        return details

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        excluded = ["cls", "self"]
        params = cls._retrieve_parameter_details(cls._process_logic, excluded)
        return {"component_type": "ContextProcessor", "parameters": params}

    @classmethod
    def context_keys(cls) -> List[str]:
        """
        Retrieve the list of valid context keys for the context processor.

        This method defines the context keys that the processor can update
        during its execution. Subclasses should implement this method to provide
        a list of keys that are relevant to their specific functionality.

        Returns:
            List[str]: A list of context keys that the processor can update.
        """
        return []

    @classmethod
    def get_created_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be created by this operation.

        By default, this returns the same as context_keys(), but subclasses
        can override to provide more specific information.

        Returns:
            List[str]: A list of context keys that the operation will add or create
                       as a result of execution.
        """
        return cls.context_keys()

    @classmethod
    def get_required_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys required by this operation.

        This method is provided for backward compatibility and inspection purposes.
        The actual parameter resolution is done at runtime based on the processor's
        parameter names and availability in context or configuration.

        Returns:
            List[str]: A list of context keys that the operation typically expects.
        """
        # For backward compatibility, return empty list by default
        # Runtime parameter resolution handles actual requirements
        return []

    @classmethod
    def get_suppressed_keys(cls) -> List[str]:
        """
        Retrieve a list of context keys that will be suppressed or removed by this operation.

        Returns:
            List[str]: A list of context keys that the operation will remove or render
                       obsolete during its execution.
        """
        return []

    def __str__(self):
        return f"{self.__class__.__name__}"
