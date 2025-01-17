# Semantiva

## Overview

The **Semantiva** is a modular and extensible framework designed to enable semantic transparency and ontology-driven processing for data operations. By leveraging concepts from ontology and context-aware computing, this framework provides tools for managing, processing, and interpreting data in a manner that aligns with predefined semantic rules and contexts.

This framework is particularly suited for applications where:
- **Semantic transparency** is essential for traceable and explainable operations.
- **Ontologies** guide the interpretation of data within well-defined domains.

## Key Features

- **Ontology Integration**: Ensures data processing aligns with domain-specific ontologies, enabling standardized interpretation.
- **Semantic Transparency**: Maintains traceability and clarity for all operations, ensuring outputs are explainable.
- **Modular Architecture**: Facilitates the addition of new data types, operations, and contexts without disrupting the existing structure.
- **Context-Aware Operations**: Incorporates contextual knowledge into data processing workflows, adapting behavior dynamically.
- **Extensibility**: Provides abstract base classes and interfaces for creating custom data types and operations.

## Components

### 1. Data Operations
Abstract classes and tools to define and execute operations on data, ensuring semantic consistency.

### 2. Context Operations
Manage contextual information that influences data processing, enabling adaptive workflows.

### 3. Payload Operations
Handle the execution and orchestration of processing nodes, encapsulating data operations and their associated contexts.

### 4. Data Types
Abstract and concrete implementations for handling different types of data with validation rules.

### 5. Execution Tools
Utility tools to streamline execution, monitoring, and debugging of data pipelines.

## License

This project is licensed under the MIT License.



---

## Appendix: Getting Started

This short guide helps you **jump right in** with a minimal example showcasing the **Semantiva’s** modular design. We’ll create and process a simple **string literal** rather than dealing with more complex domains like audio or images.


```python
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
# Step 2: Create a Specialized StringLiteralAlgorithm Using AlgorithmTopologyFactory
#########################
from semantiva.data_operations import AlgorithmTopologyFactory

# Dynamically create a base algorithm class for (StringLiteralDataType -> StringLiteralDataType)
StringLiteralAlgorithm = AlgorithmTopologyFactory.create_algorithm(
    input_type=StringLiteralDataType,
    output_type=StringLiteralDataType,
    class_name="StringLiteralAlgorithm",
)


#########################
# Step 3: Define HelloOperation (Extending StringLiteralAlgorithm)
#########################
class HelloOperation(StringLiteralAlgorithm):
    """
    A simple operation that modifies the input string to greet the inout
    and returns the updated value as a new StringLiteralDataType.
    """

    def _operation(self, data: StringLiteralDataType) -> StringLiteralDataType:
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
        "operation": HelloOperation,
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
```

---

## Summary

In these five simple steps, you’ve:

1. **Created** a custom data type for strings (`StringLiteralDataType`).
2. **Leveraged** the built-in `AlgorithmTopologyFactory` to generate a `StringLiteralAlgorithm`.
3. **Extended** that generic algorithm to define a specific operation (`HelloOperation`).
4. **Built** a **node configuration** referencing `HelloOperation`.
5. **Instantiated** a minimal pipeline and **executed** it, confirming everything works.

This approach shows how easy it is to **scale** from a “Hello World” scenario to more complex data transformations—just define new data types, create operations through the **factory**, and configure the pipeline. Once comfortable, you can **explore** domain-specific modules (audio, image, text, etc.) and advanced features like context observers or parallel execution.


---

## Acknowledgments

This framework was inspired by the need for transparency and traceability in data-driven systems of the ALICE O2 computing system. It incorporates principles of ontology-driven design to ensure robust and interpretable workflows.