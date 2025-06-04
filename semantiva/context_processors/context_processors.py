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
from typing import Dict, Any, List, Optional, Union
from semantiva.context_processors.context_types import ContextType
from semantiva.workflows.fitting_model import FittingModel
from semantiva.data_types.data_types import BaseDataType
from semantiva.core import SemantivaObject
from semantiva.logger import Logger


class ContextProcessor(SemantivaObject):
    """
    Base class for performing context operations.
    """

    logger: Logger

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger if logger else Logger()

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
            "input_parameters": annotated_parameter_list or "None",
        }
        return component_metadata


class ModelFittingContextProcessor(ContextProcessor):
    """ContextProcessor that fits extracted features using a specified model."""

    def __init__(
        self,
        logger,
        fitting_model,
        independent_var_key,
        dependent_var_key: Union[str, tuple],
        context_keyword: str,
    ):
        self.logger = logger if logger else Logger()
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.fitting_model: FittingModel = fitting_model
        self.independent_var_key = independent_var_key
        self.context_keyword = context_keyword

        if isinstance(dependent_var_key, tuple):
            self.dependent_var_key = dependent_var_key[0]
            self.dependent_var_subkey = dependent_var_key[1]
        else:
            self.dependent_var_key = dependent_var_key
            self.dependent_var_subkey = None

        if not isinstance(independent_var_key, str):
            raise TypeError(
                f"independent_var_key must be a string, got {type(independent_var_key).__name__} with value {independent_var_key}"
            )

    def _process_logic(self, context):
        """Fit extracted features to the model using context data."""

        # Retrieve independent and dependent variables from context
        independent_variable = context.get_value(self.independent_var_key)
        dependent_variable = context.get_value(self.dependent_var_key)

        # Ensure required parameters exist
        if independent_variable is None or dependent_variable is None:
            missing_params = [
                p for p in self.get_required_keys() if context.get_value(p) is None
            ]
            raise ValueError(
                f"Missing required context parameters: {', '.join(str(missing_params))}"
            )
        # Extract dependent_variable from dictionary if needed
        if isinstance(self.dependent_var_subkey, tuple):
            dependent_variable_ = tuple(
                dependent_variable[key] for key in self.dependent_var_subkey
            )
        elif isinstance(self.dependent_var_subkey, str):
            dependent_variable_ = [
                item[self.dependent_var_subkey] for item in dependent_variable
            ]
        elif isinstance(dependent_variable, list):
            dependent_variable_ = dependent_variable
        else:
            raise ValueError("Invalid type for dependent_variable")

        # Fit the model using extracted features
        self.logger.debug("\tRunning model %s", self.fitting_model)
        self.logger.debug(f"\t\tindependent_variable = {independent_variable}")
        self.logger.debug(f"\t\tdependent_variable = {dependent_variable_}")
        fit_results = self.fitting_model.fit(independent_variable, dependent_variable_)

        # Store the results back in context under the dependent variable name
        context.set_value(self.context_keyword, fit_results)

        return context

    def get_required_keys(self) -> List[str]:
        """
        Retrieve the list of required keys for the context operation.

        Returns:
            List[str]: A list containing the keys for the independent and dependent variables.

        """
        return [
            self.independent_var_key,
            self.dependent_var_key,
        ]

    def get_created_keys(self) -> List[str]:
        """
        Retrieves the list of keys created in the context.

        This method returns a list containing the keyword used to store the fit results in the context.

        Returns:
            List[str]: A list containing the context keyword.
        """
        return [self.context_keyword]

    def get_suppressed_keys(self) -> List[str]:
        """
        This operation does not suppress any keys.

        Returns:
            List[str]: An empty list as no keys are suppressed or removed by this operation.
        """
        return []
