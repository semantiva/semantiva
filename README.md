# Semantiva

## Overview

**Semantiva** is an open-source, Python-based framework that unifies **Domain-Driven Design**, **Type-Oriented Development**, and **semantic transparency** to streamline data operations. It offers a structured way to define and process domain-specific data types and algorithms, ensuring clarity, consistency, and adaptability even in complex data-driven scenarios.

By enforcing **type-safe** relationships between data and algorithms, Semantiva simplifies the creation of transparent, interpretable workflows—enabling teams to focus on solving domain problems rather than battling ambiguous data models. Semantiva also employs a **dual-channel pipeline** concept, where data and metadata context flow in parallel. This allows **dynamic parameter injection**—so each operation can fetch necessary parameters from a continuously evolving metadata context stream. Such an approach **increases reusability** (the same operation can be driven by different metadata to serve multiple use cases) and supports on-the-fly configuration changes without code rewrites.

Additionally, Semantiva is designed to be **AI-compatible**, allowing for collaboration with intelligent systems that can reason about, optimize, and even co-develop complex workflows using its well-defined semantic structures.

## Key Principles

1. **Domain-Driven Design (DDD)**
   - Aligns data types, algorithms, and operations with core domain concepts.
   - Ensures each module speaks a consistent “domain language,” reducing misunderstandings and promoting maintainability.

2. **Type-Oriented Development**
   - Establishes robust contracts between data and operations.
   - Minimizes errors by validating data structures at definition time, preventing mismatches or incompatible operations.

3. **Semantic Transparency & AI-Readiness**
   - Retains full traceability of how data is transformed and why particular operations are invoked.
   - Facilitates clear, explainable workflows, valuable for AI-driven assistance, QA, audits, or scientific reproducibility.
   - Enables AI assistants to understand, suggest, and even co-design workflows based on structured metadata and domain logic.

4. **Modular & Extensible Architecture**
   - Supports adding new data types, operation types, and domain ontologies without disrupting existing components.
   - Adapts naturally to diverse applications—ranging from basic string manipulations to advanced imaging pipelines or HPC-scale workloads.
   - Allows intelligent agents to interact with and modify workflows dynamically, making it a natural fit for AI-assisted design and automation.

## Why Semantiva?

- **Clarity & Consistency**: Well-defined semantics for data and operations ensure that both humans and AI systems understand precisely how information flows and transforms.
- **Adaptive Workflows**: Easily extend pipelines with new steps or data types, minimizing rework when domain requirements evolve.
- **Scalability & HPC Integration**: Abstract base classes and a pipeline-oriented design let users scale operations seamlessly, whether on local machines or high-performance clusters.
- **AI-Driven Collaboration**: Semantiva’s structured approach enables AI systems to assist with workflow optimizations, debugging, and dynamic pipeline generation.
- **Interdisciplinary Collaboration**: A shared language of data and operation types fosters better communication across physics, mathematics, engineering, and software teams.
- **Dual-Channel Pipelines**: Semantiva doesn’t just process data; it manages **metadata context** in parallel. This powerful design lets you inject dynamic parameters into each operation, influence routing or thresholds at runtime, and evolve configurations mid-pipeline—**ideal for software architects** who need flexible system designs and for **researchers** exploring iterative experiments.  
- **Dynamic Parameter Injection**: By pulling parameters directly from the metadata context stream (instead of hardcoding them), each operation becomes more composable and reusable. **Systems engineers** can update or override settings without redeploying the entire pipeline, and **developers** can write once and adapt many times.  
- **Advanced Reusability**: Operations remain generic because specific behaviors (thresholds, routing decisions, or domain-specific parameters) live in the metadata context flow. This reduces code duplication and fosters a library of well-tested transformations that can be combined for new use cases.

## AI-Enhanced Development Potential

Semantiva is not just an execution framework—it is also an **AI-compatible co-design environment** that enables advanced AI assistants to:

- **Understand Workflow Semantics**: AI can analyze the framework’s structural metadata, reasoning about data flow, dependencies, and logical constraints.
- **Generate & Modify Pipelines**: Given a high-level task description, AI can suggest or even implement workflow modifications that align with Semantiva’s principles.
- **Explain & Debug Operations**: AI can trace execution paths, highlight inefficiencies, and generate human-readable explanations of complex workflows.
- **Enhance Cross-Domain Usability**: By maintaining semantic clarity, AI systems can generalize Semantiva’s use cases across industries without needing deep domain-specific re-engineering.

This makes Semantiva uniquely suited to the evolving landscape of **human-AI collaboration**, ensuring that future AI-driven applications remain interpretable, adaptable, and semantically sound.

## Core Components

1. **Data Operations**
   - Abstract classes that enforce type-safe transformations, ensuring data flows remain coherent and domain-accurate.

2. **Context Operations**
   - Manages contextual or environmental information affecting data processing, enhancing adaptability and domain awareness.

3. **Payload Operations (Pipelines)**
   - Orchestrates the execution of multiple operations, combining data transformations and context adaptations into a coherent workflow.
   - Semantiva pipelines propagate both **data** and **metadata context** in parallel, empowering operations to dynamically fetch parameters. This supports fluid, on-the-fly changes to how data is processed.

4. **Data Types & Operation Types**
   - Defines the structure and constraints of domain-specific data, alongside compatible operations (e.g., `Image` ↔ `ImageOperation`), guaranteeing semantic integrity.

5. **Execution Tools**
   - Utilities for executing, monitoring, and debugging pipelines, supporting straightforward deployment and scaling.

## License

Semantiva is released under the [MIT License](./LICENSE), promoting collaborative development and broad adoption.

---

## Getting Started: A Minimal Example

Below is a quick demonstration showing how Semantiva can handle a simple string data type and a matching operation. For more advanced domains—like imaging, wafer metrology, or large-scale simulations—users can define new data and operation types to match their specific needs.


 
```python
 
# 1) Define StringLiteralDataType
 
from semantiva.data_types import BaseDataType
 

 
class StringLiteralDataType(BaseDataType):
 
    def __init__(self, data: str):
 
        super().__init__(data)
 

 
    def validate(self, data):
 
        assert isinstance(data, str), "Data must be a string."
 

 

 
# 2) Create a StringLiteralOperation
 
from semantiva.data_processors import OperationTopologyFactory
 

StringLiteralOperation = OperationTopologyFactory.create_data_operation(
 
    input_type=StringLiteralDataType,
 
    output_type=StringLiteralDataType,
 
    class_name="StringLiteralOperation",
 
)
 
# 3) Define an Operation Extending StringLiteralOperation

 
class HelloOperation(StringLiteralOperation):

    def _process_logic(self, data: StringLiteralDataType) -> StringLiteralDataType:
 
        return StringLiteralDataType(f"Hello, {data.data}")
 

# 4) Build a Minimal Pipeline
 
from semantiva.payload_operations import Pipeline
 
node_configurations = [
 
    {
        "processor": HelloOperation,
        "parameters": {},
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

* **Dual-Channel Processing**: Semantiva simultaneously processes **data** (the generated image stack) and **metadata** (like `t_values` and fitting parameters), ensuring each pipeline step can **dynamically** adapt based on evolving context.  
* **Parametric Generation & Feature Extraction**: You can generate synthetic images via symbolic expressions, then extract domain-specific features (e.g., Gaussian parameters) in one coherent workflow.  
* **Dynamic Parameter Injection**: Each node reads from and writes to a shared metadata context. That means you can modify or extend these parameters (e.g., changing the polynomial degree or image size) **without** altering code logic.  
* **Multi-Stage Modeling**: By chaining multiple `ModelFittingContextProcessor` steps, you can fit various features to different independent variables—particularly useful for research or production pipelines where multiple relationships must be modeled.  
* **Traceable & Auditable**: The final pipeline `context` retains the entire metadata history—including extracted features and fitted coefficients. This allows for transparent auditing, reproducibility, and potential handoff to subsequent pipelines or AI tools.

> With Semantiva’s **dual-channel** approach, you gain the flexibility to adapt pipeline logic on the fly. Even advanced tasks—such as parametric signal generation, feature extraction, and multi-stage model fitting—become modular, maintainable, and straightforward to extend.

## Summary

**Semantiva** delivers a structured, type-safe, and domain-driven environment for designing adaptable data pipelines. By emphasizing semantic transparency and explicit domain alignment, it reduces cognitive load, fosters cross-disciplinary collaboration, and enables confident scaling to more complex or HPC-intensive problems—without sacrificing clarity or maintainability. Whether implementing straightforward text operations or tackling sophisticated scientific and industrial tasks, Semantiva equips developers and researchers with the tools to build robust, interpretable, and future-ready data solutions.


---

## Acknowledgments

This framework draws inspiration from the rigorous demands of transparency and traceability in data-driven systems, particularly exemplified by the ALICE O2 project at CERN. The lessons learned from managing large-scale, high-throughput data in that environment—combined with the need for robust, domain-aligned workflows—shaped Semantiva’s emphasis on type-safe design, semantic clarity, and modular extensibility. By blending these concepts with principles of ontology-driven computing, Semantiva aims to deliver the same level of reliability and interpretability for any domain requiring advanced data processing and HPC integration.
