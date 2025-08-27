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

from collections import ChainMap
from typing import Any, Dict, Optional, Union
from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.logger import Logger
from .context_types import ContextType, ContextCollectionType


class _ContextObserver(_SemantivaComponent):
    """Base class for all nodes in semantiva pipelines responsible for context propagation and updates."""

    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the observer with an empty context."""
        super().__init__(logger)
        self.observer_context = ContextType()

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        """
        Define metadata for the _ContextObserver class.

        Returns:
            dict: Metadata dictionary containing component type and context type.
        """
        component_metadata = {
            "component_type": "ContextObserver",
        }
        return component_metadata

    @staticmethod
    def delete_context(
        context: Union[ContextType, ContextCollectionType, ChainMap],
        key: str,
        index: Optional[int] = None,
    ):
        """
        Deletes a context key in either a single or collection context.

        - If `context` is a `ChainMap`, deletion must be done on the **local context** (first mapping).
        - If `context` is `ContextCollectionType`, deletion is applied globally or to a slice.

        Args:
            context (Union[ContextType, ContextCollectionType, ChainMap]): The context to update.
            key (str): The key to delete.
            index (Optional[int]): The index of the slice to update (if context is a collection).

        Raises:
            ValueError: If attempting to delete from a collection without specifying an index.
            KeyError: If the key does not exist in the context.
        """
        if isinstance(context, ContextCollectionType):
            if index is None:
                context.delete_value(key)
            else:
                context.delete_item_value(index, key)
        elif isinstance(context, ChainMap):
            # ChainMap deletion from the first mapping (local context)
            if key in context.maps[0]:
                del context.maps[0][key]
            else:
                raise KeyError(f"Key '{key}' not found in local context")
        else:
            context.delete_value(key)

    @staticmethod
    def update_context(
        context: Union[ContextType, ContextCollectionType, ChainMap],
        key: str,
        value: Any,
        index: Optional[int] = None,
    ):
        """
        Updates a context value in either a single or collection context.

        - If `context` is a `ChainMap`, writes must be done on the **local context** (first mapping).
        - If `context` is `ContextCollectionType`, updates are applied globally or to a slice.

        Args:
            context (Union[ContextType, ContextCollectionType, ChainMap]): The context to update.
            key (str): The key to update.
            value (Any): The value to set.
            index (Optional[int]): The index of the slice to update (if context is a collection).

        Raises:
            ValueError: If attempting to update a collection without specifying an index.


        """
        if isinstance(context, ContextCollectionType):
            if index is None:
                context.set_value(key, value)
            else:
                context.set_item_value(index, key, value)
        elif isinstance(context, ChainMap):
            # ChainMap writes the first mapping (local context)
            context.maps[0][key] = value
        else:
            context.set_value(key, value)

    def update(self, key: str, value: Any, index: Optional[int] = None) -> None:
        """Update the stored context via :meth:`update_context`."""
        self.update_context(self.observer_context, key, value, index)

    def delete(self, key: str, index: Optional[int] = None) -> None:
        """Delete a key from the stored context via :meth:`delete_context`."""
        self.delete_context(self.observer_context, key, index)


class _ValidatingContextObserver(_ContextObserver):
    """Context observer that validates updates and deletions against registered keys."""

    def __init__(
        self,
        context_keys: list[str],
        suppressed_keys: list[str],
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the validating observer with allowed keys.

        Args:
            context_keys: List of keys that can be updated by the processor
            suppressed_keys: List of keys that can be deleted by the processor
            logger: Optional logger instance
        """
        super().__init__(logger)
        self._allowed_context_keys = set(context_keys)
        self._allowed_suppressed_keys = set(suppressed_keys)

    def update(self, key: str, value: Any, index: Optional[int] = None) -> None:
        """Update context with validation against registered context keys."""
        if key not in self._allowed_context_keys:
            raise KeyError(
                f"Invalid context key '{key}' for processor. "
                f"Allowed keys: {sorted(self._allowed_context_keys)}"
            )
        super().update(key, value, index)

    def delete(self, key: str, index: Optional[int] = None) -> None:
        """Delete context key with validation against registered suppressed keys."""
        if key not in self._allowed_suppressed_keys:
            raise KeyError(
                f"Invalid suppressed key '{key}' for processor. "
                f"Allowed suppressed keys: {sorted(self._allowed_suppressed_keys)}"
            )
        super().delete(key, index)
