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
        """
        Initialize the _ContextObserver with an empty context.

        Attributes:
            context (dict): A dictionary to store contextual key-value pairs.
        """
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
