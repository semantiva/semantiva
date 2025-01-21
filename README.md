# Semantiva

## Overview

**Semantiva** is an open-source, Python-based framework that unifies **Domain-Driven Design**, **Type-Oriented Development**, and **semantic transparency** to streamline data operations. It offers a structured way to define and process domain-specific data types and algorithms, ensuring clarity, consistency, and adaptability even in complex data-driven scenarios.

By enforcing **type-safe** relationships between data and algorithms, Semantiva simplifies the creation of transparent, interpretable workflows—enabling teams to focus on solving domain problems rather than battling ambiguous data models.

## Key Principles

1. **Domain-Driven Design (DDD)**
   - Aligns data types, algorithms, and operations with core domain concepts.
   - Ensures each module speaks a consistent “domain language,” reducing misunderstandings and promoting maintainability.

2. **Type-Oriented Development**
   - Establishes robust contracts between data and algorithms.
   - Minimizes errors by validating data structures at definition time, preventing mismatches or incompatible operations.

3. **Semantic Transparency**
   - Retains full traceability of how data is transformed and why particular operations are invoked.
   - Facilitates clear, explainable workflows, valuable for QA, audits, or scientific reproducibility.

4. **Modular & Extensible Architecture**
   - Supports adding new data types, algorithm types, and domain ontologies without disrupting existing components.
   - Adapts naturally to diverse applications—ranging from basic string manipulations to advanced imaging pipelines or HPC-scale workloads.

## Why Semantiva?

- **Clarity & Consistency**: Well-defined semantics for data and algorithms ensure that everyone understands precisely how information flows and transforms.
- **Adaptive Workflows**: Easily extend pipelines with new steps or data types, minimizing rework when domain requirements evolve.
- **Scalability & HPC Integration**: Abstract base classes and a pipeline-oriented design let users scale operations seamlessly, whether on local machines or high-performance clusters.
- **Interdisciplinary Collaboration**: A shared language of data and algorithm types fosters better communication across physics, mathematics, engineering, and software teams.

## Core Components

1. **Data Operations**
   - Abstract classes that enforce type-safe transformations, ensuring data flows remain coherent and domain-accurate.

2. **Context Operations**
   - Manages contextual or environmental information affecting data processing, enhancing adaptability and domain awareness.

3. **Payload Operations (Pipelines)**
   - Orchestrates the execution of multiple operations, combining data transformations and context adaptations into a coherent workflow.

4. **Data Types & Algorithm Types**
   - Defines the structure and constraints of domain-specific data, alongside compatible algorithms (e.g., `Image` ↔ `ImageAlgorithm`), guaranteeing semantic integrity.

5. **Execution Tools**
   - Utilities for executing, monitoring, and debugging pipelines, supporting straightforward deployment and scaling.

## License

Semantiva is released under the [MIT License](./LICENSE), promoting collaborative development and broad adoption.

---

## Getting Started: A Minimal Example

Below is a quick demonstration showing how Semantiva can handle a simple string data type and a matching algorithm. For more advanced domains—like imaging, wafer metrology, or large-scale simulations—users can define new data and algorithm types to match their specific needs.

```python
# 1) Define StringLiteralDataType
from semantiva.data_types import BaseDataType

class StringLiteralDataType(BaseDataType):
    def __init__(self, data: str):
        super().__init__(data)

    def validate(self, data):
        assert isinstance(data, str), "Data must be a string."


# 2) Create a StringLiteralAlgorithm
from semantiva.data_operations import AlgorithmTopologyFactory

StringLiteralAlgorithm = AlgorithmTopologyFactory.create_algorithm(
    input_type=StringLiteralDataType,
    output_type=StringLiteralDataType,
    class_name="StringLiteralAlgorithm",
)


# 3) Define an Operation Extending StringLiteralAlgorithm
class HelloOperation(StringLiteralAlgorithm):
    def _operation(self, data: StringLiteralDataType) -> StringLiteralDataType:
        return StringLiteralDataType(f"Hello, {data.data}")


# 4) Build a Minimal Pipeline
from semantiva.payload_operations import Pipeline
from semantiva.context_operations import ContextPassthrough

node_configurations = [
    {
        "operation": HelloOperation,
        "parameters": {},
        "context_operation": ContextPassthrough,
    },
]

if __name__ == "__main__":
    pipeline = Pipeline(node_configurations)
    input_data = StringLiteralDataType("World!")
    output_data, _ = pipeline.process(input_data, {})
    print("Pipeline completed. Final output:", output_data.data) # "Hello, World!"

```


---

### Key Takeaways

* **Strong Type Contracts**: The `StringLiteralDataType` enforces the string constraint; incompatible data will fail early.
* **Algorithm-Data Alignment**: `HelloOperation` inherits from `StringLiteralAlgorithm`, ensuring it can only act on `StringLiteralDataType`.
* **Scalable Pipeline**: Extend this structure with domain-specific types (e.g., `Image`, `Spectrum`, `AudioClip`) and matching algorithms as needs grow.

## Summary

**Semantiva** delivers a structured, type-safe, and domain-driven environment for designing adaptable data pipelines. By emphasizing semantic transparency and explicit domain alignment, it reduces cognitive load, fosters cross-disciplinary collaboration, and enables confident scaling to more complex or HPC-intensive problems—without sacrificing clarity or maintainability. Whether implementing straightforward text operations or tackling sophisticated scientific and industrial tasks, Semantiva equips developers and researchers with the tools to build robust, interpretable, and future-ready data solutions.


---

## Acknowledgments

This framework draws inspiration from the rigorous demands of transparency and traceability in data-driven systems, particularly exemplified by the ALICE O2 project at CERN. The lessons learned from managing large-scale, high-throughput data in that environment—combined with the need for robust, domain-aligned workflows—shaped Semantiva’s emphasis on type-safe design, semantic clarity, and modular extensibility. By blending these concepts with principles of ontology-driven computing, Semantiva aims to deliver the same level of reliability and interpretability for any domain requiring advanced data processing and HPC integration.
