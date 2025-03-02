#########################
# Step 1: Define StringLiteralDataType
#########################
from semantiva.data_types import BaseDataType


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
from semantiva.data_processors import OperationTopologyFactory

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
    A simple operation that modifies the input string to greet the inout
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
from semantiva.payload_operations import Pipeline

if __name__ == "__main__":
    # 1. Initialize the minimal pipeline with our node configurations
    pipeline = Pipeline(node_configurations)

    # 2. Create a StringLiteralDataType object
    input_data = StringLiteralDataType("World!")

    # 3. Run the pipeline
    output_data, _ = pipeline.process(input_data, {})

    # 4. Print final result
    print("Pipeline completed. Final output:", output_data.data)


def test_string_specialization():
    # 1. Initialize the pipeline with our node configurations
    pipeline = Pipeline(node_configurations)

    # 2. Create a StringLiteralDataType object
    input_data = StringLiteralDataType("World!")

    # 3. Run the pipeline
    output_data, _ = pipeline.process(input_data, {})

    # 4. Print final result
    print("Pipeline completed. Final output:", output_data.data)

    # Check that the output matches the expected greeting
    assert output_data.data == "Hello, World!"
