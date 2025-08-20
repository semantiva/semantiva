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
from typing import Any, Dict, List, Optional

from semantiva.context_processors.context_types import ContextType
from semantiva.data_types.data_types import BaseDataType
from semantiva.core.semantiva_component import _SemantivaComponent
from semantiva.logger import Logger


class ContextProcessor(_SemantivaComponent):
    """
    Base class for performing context operations.
    """

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)

    @abstractmethod
    def _process_logic(self, context: ContextType) -> ContextType:
        """
        Perform the core logic of the context operation.

        This method must be implemented by subclasses to define the specific
        operation to be performed on the given context.

        Args:
            context (ContextType): The context on which the operation is performed.

        Returns:
            ContextType: The modified (or unchanged) context after the operation.
        """

    @classmethod
    def input_data_type(cls):
        """Return the placeholder data type accepted by context processors."""
        return BaseDataType

    def get_processing_parameter_names(self) -> List[str]:
        """
        Retrieve the names of parameters required by the operation.

        Returns:
            List[str]: A list of parameter names (excluding `data`).
        """
        return self.get_required_keys()

    def operate_context(self, context: ContextType) -> ContextType:
        """
        Execute the context operation.

        Calls the subclass-implemented `_process_logic` method to perform the
        operation on the provided context.

        Args:
            context (ContextType): The context to operate on.

        Returns:
            ContextType: The result of the context operation.
        """
        self.logger.debug(f"Executing {self.__class__.__name__}")
        return self._process_logic(context)

    @abstractmethod
    def get_required_keys(self) -> List[str]:
        """
        Retrieve a list of context keys required by this operation.

        Returns:
            List[str]: A list of context keys that the operation expects to be present
                       before execution.
        """

    @abstractmethod
    def get_created_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be created by this operation.

        Returns:
            List[str]: A list of context keys that the operation will add or create
                       as a result of execution.
        """

    @abstractmethod
    def get_suppressed_keys(self) -> List[str]:
        """
        Retrieve a list of context keys that will be suppressed or removed by this operation.

        Returns:
            List[str]: A list of context keys that the operation will remove or render
                       obsolete during its execution.
        """

    def __str__(self):
        return f"{self.__class__.__name__}"

    @classmethod
    def _define_metadata(cls) -> Dict[str, Any]:
        excluded_parameters = ["cls", "self", "data"]

        annotated_parameter_list = [
            f"{param_name}: {param_type}"
            for param_name, param_type in cls._retrieve_parameter_signatures(
                cls._process_logic, excluded_parameters
            )
        ]

        component_metadata = {
            "component_type": "ContextProcessor",
            "parameters": annotated_parameter_list or "None",
        }
        return component_metadata
