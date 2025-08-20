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

#########################
# Step 1: Define StringLiteralDataType
#########################
from typing import TYPE_CHECKING

from semantiva.data_types import BaseDataType
from semantiva.pipeline import Pipeline, Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.data_processors import DataOperation, OperationTopologyFactory


class StringLiteralDataType(BaseDataType):
    """
    Represents a simple string literal data type.

    This class encapsulates a Python string, ensuring type consistency
    and providing a base for operations on string data.
    """

    def __init__(self, data: str):
        """
        Initialize the StringLiteralDataType with the provided string.

        Args:
            data (str): The string data to encapsulate.
        """
        super().__init__(data)

    def validate(self, data):
        """
        Validate that the provided data is a string literal.

        Args:
            data: The value to validate.
        """
        assert isinstance(data, str), "Data must be a string."


#########################
# Step 2: Create a Specialized StringLiteralOperation Using OperationTopologyFactory
#########################

if TYPE_CHECKING:

    class StringLiteralOperation(DataOperation):
        @classmethod
        def input_data_type(cls) -> type[StringLiteralDataType]: ...

        @classmethod
        def output_data_type(cls) -> type[StringLiteralDataType]: ...

        def _process_logic(
            self, data: StringLiteralDataType
        ) -> StringLiteralDataType: ...

else:
    # Dynamically create a base operation class for (StringLiteralDataType -> StringLiteralDataType)
    StringLiteralOperation = OperationTopologyFactory.create_data_operation(
        input_type=StringLiteralDataType,
        output_type=StringLiteralDataType,
        class_name="StringLiteralOperation",
    )


#########################
# Step 3: Define HelloOperation (Extending StringLiteralOperation)
#########################
class HelloOperation(StringLiteralOperation):
    """
    A simple operation that modifies the input string to greet the input
    and returns the updated value as a new StringLiteralDataType.
    """

    def _process_logic(self, data: StringLiteralDataType) -> StringLiteralDataType:
        """
        Prepends "Hello, " to the input string and returns it as a new StringLiteralDataType.

        Args:
            data (StringLiteralDataType): The input data containing a Python string.

        Returns:
            StringLiteralDataType: The updated data containing the greeting.
        """
        hello_data = f"Hello, {data.data}"
        return StringLiteralDataType(hello_data)


#########################
# Step 4: Create a Pipeline Configuration Using HelloOperation
#########################

node_configurations = [
    {
        "processor": HelloOperation,
        "parameters": {},  # No extra parameters needed
    },
]


#########################
# Step 5: Instantiate and Use the Pipeline
#########################

if __name__ == "__main__":
    # 1. Initialize the minimal pipeline with our node configurations
    pipeline = Pipeline(node_configurations)

    # 2. Create a StringLiteralDataType object
    input_data = StringLiteralDataType("World!")

    # 3. Run the pipeline
    payload = pipeline.process(Payload(input_data, ContextType({})))
    output_data = payload.data

    # 4. Print final result
    print("Pipeline completed. Final output:", output_data.data)


def test_string_extension():
    # 1. Initialize the pipeline with our node configurations
    pipeline = Pipeline(node_configurations)

    # 2. Create a StringLiteralDataType object
    input_data = StringLiteralDataType("World!")

    # 3. Run the pipeline
    payload = pipeline.process(Payload(input_data, ContextType({})))
    output_data = payload.data

    # 4. Print final result
    print("Pipeline completed. Final output:", output_data.data)

    # Check that the output matches the expected greeting
    assert output_data.data == "Hello, World!"
