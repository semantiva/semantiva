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

## Getting Started: A Parameterized Feature Extract-and-Fit Workflow

This is an advanced example demonstrating how Semantiva can generate images **based on metadata parameters**, extract features, and fit a simple model—all within a single pipeline. Notice how **context metadata** flows alongside **data**, allowing each operation to dynamically pull parameters from the context.

```python
from semantiva.logger import Logger
from semantiva.specializations.image.image_probes import (
    TwoDTiltedGaussianFitterProbe,
)
from semantiva.workflows.fitting_model import PolynomialFittingModel
from semantiva.context_processors.context_processors import ModelFittingContextProcessor
from semantiva.payload_operations.pipeline import Pipeline

from semantiva.specializations.image.image_loaders_savers_generators import (
    TwoDGaussianImageGenerator,
    ParametricImageStackGenerator,
)

# --- 1) Parametric Image Generation ---
# We create a stack of images with a time-varying 2D Gaussian signal.
# 'ParametricImageStackGenerator' uses symbolic expressions to vary the Gaussian's position,
# standard deviation, angle, etc. over multiple frames (num_frames=10).
generator = ParametricImageStackGenerator(
    num_frames=3,
    parametric_expressions={
        "x_0": "50 + 5 * t",                # Time-dependent center x position
        "y_0": "50 + 5 * t + 5  * t ** 2",  # Time-dependent center y position
        "std_dev": "(50 + 20 * t, 20)",     # Stdev changes over frames
        "amplitude": "100",                 # Constant amplitude
        "angle": "60 + 5 * t",              # Orientation angle changes over frames
    },
    param_ranges={
        "t": (-1, 2)
    },  # 't' will sweep from -1 to +2, controlling the parametric expressions
    image_generator=TwoDGaussianImageGenerator(),
    image_generator_params={"image_size": (128, 128)},  # Image resolution
)

# Retrieve the generated stack of 2D images and the corresponding time values.
image_stack = generator.get_data()
t_values = generator.t_values  # List/array of 't' values used in generation.

# Prepare a context dictionary that includes 't_values' (the independent variable)
# for later use when fitting polynomial models to extracted features.
context_dict = {"t_values": t_values}

# --- 2) Define the Pipeline Configuration ---
# Our pipeline has three steps:
#   1. TwoDTiltedGaussianFitterProbe: Extracts Gaussian parameters (std_dev, angle, etc.) from each frame.
#   2. ModelFittingContextProcessor: Fits a polynomial model to the extracted std_dev_x feature vs. t_values.
#   3. Another ModelFittingContextProcessor: Fits a polynomial model to the extracted angle feature vs. t_values.
node_configurations = [
    {
        "processor": TwoDTiltedGaussianFitterProbe,
        # This probe extracts best-fit parameters for the 2D Gaussian in each frame
        # and stores them in the pipeline context under 'gaussian_fit_parameters'.
        "context_keyword": "gaussian_fit_parameters",
    },
    {
        "processor": ModelFittingContextProcessor,
        "parameters": {
            # Use a linear (degree=1) model to fit the extracted std_dev_x vs. t_values.
            "fitting_model": PolynomialFittingModel(degree=1),
            "independent_var_key": "t_values",
            "dependent_var_key": ("gaussian_fit_parameters", "std_dev_x"),
            "context_keyword": "std_dev_coefficients",
        },
    },
    {
        "processor": ModelFittingContextProcessor,
        "parameters": {
            # Also use a linear model to fit the orientation angle vs. t_values.
            "fitting_model": PolynomialFittingModel(degree=1),
            "independent_var_key": "t_values",
            "dependent_var_key": ("gaussian_fit_parameters", "angle"),
            "context_keyword": "orientation_coefficients",
        },
    },
]

# --- 3) Create and Run the Pipeline ---
pipeline = Pipeline(node_configurations)

# Pass the image stack (data) and the context dictionary (metadata) to the pipeline.
# Each pipeline step can read/write both data and context, enabling dynamic parameter injection.
output_data, output_context = pipeline.process(image_stack, context_dict)

# --- 4) Inspect Results ---
# 'std_dev_coefficients' and 'orientation_coefficients' were computed during pipeline execution.
# They store the best-fit linear coefficients for each feature.
print("Fitting Results for std_dev_x:",
      output_context.get_value("std_dev_coefficients"))
print("Fitting Results for orientation:",
      output_context.get_value("orientation_coefficients"))
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
