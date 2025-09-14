# Semantiva

## Overview

**Semantiva** is an open-source, Python-based framework that unifies **Domain-Driven Design**, **Type-Oriented Development**, and **semantic transparency** to streamline data operations. It offers a structured way to define and process domain-specific data types and algorithms, ensuring clarity, consistency, and adaptability even in complex data-driven scenarios.

By enforcing **type-safe** relationships between data and algorithms, Semantiva simplifies the creation of transparent, interpretable workflows—enabling teams to focus on solving domain problems rather than battling ambiguous data models. Semantiva also employs a **dual-channel pipeline** concept, where data and metadata context flow in parallel. This allows **dynamic parameter injection**—so each operation can fetch necessary parameters from a continuously evolving metadata context stream. Such an approach **increases reusability** (the same operation can be driven by different metadata to serve multiple use cases) and supports on-the-fly configuration changes without code rewrites.

Additionally, Semantiva is designed to be **AI-compatible**, allowing for collaboration with intelligent systems that can reason about, optimize, and even co-develop complex workflows using its well-defined semantic structures.

## Why Semantiva?

Semantiva is more than a pipeline runner—it is a **semantic framework for reproducible, contract-validated data workflows**.
Pipelines compile into **deterministic graphs with stable IDs**, components are checked against a **contract catalog**, and payloads always flow with **typed data and structured context**.
With first-class **parametric sweeps** and pluggable **execution backends**, Semantiva combines **clarity, provenance, and flexibility** in one framework.


## Key Principles

1. **Domain-Driven Design (DDD)**
   - Aligns data types, algorithms, and operations with core domain concepts.
   - Ensures each module speaks a consistent “domain language,” reducing misunderstandings and promoting maintainability.

2. **Type-Oriented Development**
   - Establishes robust contracts between data and operations.
   - Minimizes errors by validating data structures at definition time, preventing mismatches or incompatible operations.

3. **Semantic Transparency & AI-Readiness**
   - Retains full traceability of how data is transformed and why particular operations are invoked.

## Features

- **Semantic Components**: Processors, data types, and contexts are `_SemantivaComponent`s with machine-readable metadata mapped to RDF predicates—ready for knowledge-graph integration.
- **Deterministic Graph Identity**: Pipelines compile into canonical graphs with stable node/pipeline IDs (UUIDv5 + SHA256). Cosmetic YAML changes won’t alter provenance.
- **Contract-Validated Processors**: A table-driven ruleset validates every component (input/output types, metadata, context usage). Results are diagnostics, not crashes.
- **Typed Payloads and Rich Context**: Workflows operate on `Payload(data, context)`, where data is a `BaseDataType` and context is a structured `ContextType`—ensuring safe parameter resolution and traceability.
- **Parametric Sweeps**: Define systematic parameter grids in YAML (ranges, sequences, context-driven variables). Sweeps generate typed collections for experimentation without boilerplate.
- **Flexible Execution**: Clean separation of concerns: Executor (how tasks run), Orchestrator (how the graph is traversed), Transport (how messages/events are passed). Ships with in-memory defaults, ready to scale out.
- **Tracing and Observability**: Optional tracing emits before/after/error events with deterministic IDs. Zero overhead when disabled.
- **Modular & Extensible Architecture**
  - Supports adding new data types, processor types, and domain ontologies without disrupting existing components.
  - Adapts naturally to diverse applications—ranging from basic string manipulations to advanced imaging pipelines or HPC-scale workloads.
  - Allows intelligent agents to interact with and modify workflows dynamically, making it a natural fit for AI-assisted design and automation.

## Benefits

- **Clarity & Consistency**: Well-defined semantics for data and operations ensure that both humans and AI systems understand precisely how information flows and transforms.
- **Adaptive Workflows**: Easily extend pipelines with new steps or data types, minimizing rework when domain requirements evolve.
- **Scalability & HPC Integration**: A pipeline-oriented design lets users scale operations seamlessly, whether on local machines or high-performance clusters.
- **AI-Driven Collaboration**: Structured metadata enables AI systems to assist with workflow optimizations, debugging, and dynamic pipeline generation.
- **Interdisciplinary Collaboration**: A shared language of data and processor types fosters better communication across physics, mathematics, engineering, and software teams.
- **Dual-Channel Pipelines**: Semantiva processes **data** and **metadata context** in parallel, enabling dynamic parameter injection and runtime adaptation without code rewrites.
- **Dynamic Parameter Injection**: Parameters come from the context stream (not hardcoded), improving composability and reuse; change behavior without redeploys.
- **Advanced Reusability**: Keep operations generic; put thresholds/routing/domain parameters in context to reduce duplication and enable mix-and-match pipelines.

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

2. **Context Processors**
   - Manage contextual or environmental information affecting data processing, enhancing adaptability and domain awareness.

3. **Pipelines**
   - Orchestrate the execution of multiple operations, combining data transformations and context adaptations into a coherent workflow.
   - Semantiva pipelines propagate both **data** and **metadata context** in parallel, empowering operations to dynamically fetch parameters. This supports fluid, on-the-fly changes to how data is processed.

4. **Data Types & Processor Types**
   - Define the structure and constraints of domain-specific data, alongside compatible operations (e.g., `Image` ↔ `ImageOperation`), guaranteeing semantic integrity.

5. **Execution Tools**
   - Utilities for executing, monitoring, and debugging pipelines, supporting straightforward deployment and scaling.

## Pipeline Configuration & Node Factories

Semantiva pipelines are defined declaratively via YAML. Users implement processors and register them; **nodes are generated by factories** based on these configurations. Class resolvers (e.g., `slicer:`, `rename:`, `delete:`) and parameter resolvers (e.g., `model:`) resolve processors and parameters at load time, eliminating manual node instantiation.

## Getting Started with Semantiva

### Run from CLI

```bash
semantiva inspect semantiva/examples/simple_pipeline.yaml
semantiva inspect --extended semantiva/examples/simple_pipeline.yaml
semantiva run semantiva/examples/simple_pipeline.yaml --context experiment=AB42 --context seed=1234
semantiva run semantiva/examples/simple_pipeline.yaml
semantiva run semantiva/examples/simple_pipeline.yaml --validate
semantiva run semantiva/examples/simple_pipeline.yaml --dry-run
```

To quickly dive into Semantiva, explore the following resources:

- **Advanced Workflow Demo:**  
   Check out the [Semantiva Imaging](https://github.com/semantiva/semantiva-imaging) repository for a detailed demo on designing advanced imaging pipelines.

- **Extended Documentation:**  
   Visit [api.semantiva.org](https://api.semantiva.org/) for comprehensive reference material on Semantiva's architecture, principles, and usage.

These resources offer a practical roadmap to mastering the framework and leveraging its full potential in your projects.
 
---

## License
Semantiva is released under the [Apache License 2.0](./LICENSE), promoting collaborative development and broad adoption.

---

## Acknowledgments

This framework draws inspiration from the rigorous demands of transparency and traceability in data-driven systems, particularly exemplified by the ALICE O2 project at CERN. The lessons learned from managing large-scale, high-throughput data in that environment—combined with the need for robust, domain-aligned workflows—shaped Semantiva’s emphasis on type-safe design, semantic clarity, and modular extensibility. By blending these concepts with principles of ontology-driven computing, Semantiva aims to deliver the same level of reliability and interpretability for any domain requiring advanced data processing and HPC integration.