# Semantiva

## Overview

**Semantiva** is an open-source, Python-based framework that unifies **Domain-Driven Design**, **Type-Oriented Development**, and **semantic transparency** to streamline data operations. It offers a structured way to define and process domain-specific data types and algorithms, ensuring clarity, consistency, and adaptability even in complex scenarios.

Semantiva enforces **type-safe relationships** between data and algorithms and uses a **dual-channel pipeline** model where payload and context flow together. This enables dynamic parameter injection, traceable execution, and high reusability across workflows.

## Install

```bash
pip install semantiva
````

---

## Getting Started

### Quickstart — Hello pipeline (YAML only)

Create `hello.yaml`:

```yaml
extensions: ["semantiva-examples"]

pipeline:
  nodes:
    - processor: FloatValueDataSource
      parameters:
        value: 1.0

    - processor: FloatAddOperation
      parameters:
        addend: 2.0

    - processor: FloatMultiplyOperation
      parameters:
        factor: 10.0

    - processor: FloatCollectValueProbe
      context_key: "result"
    - processor: template:"result_{result}.txt":path
    - processor: FloatTxtFileSaver
```

Run it:

```bash
semantiva run hello.yaml
```

This writes the computed result to the output file defined dynamically by the context.

For the complete guide, visit **[https://api.semantiva.org](https://api.semantiva.org/getting_started.html)**

---

## Why Semantiva?

Semantiva is a **semantic framework for reproducible, contract-validated workflows**:

* Pipelines compile into **deterministic graphs** with stable semantic/configuration IDs.
* Components are validated through a **contract catalog**.
* Payload and context travel together to enable **dynamic behavior** and rich introspection.
* Supports **parametric sweeps**, **context-driven adaptation**, and **pluggable execution backends**.

---

## Key Principles

1. **Domain-Driven Design (DDD)**
2. **Type-Oriented Development**
3. **Semantic Transparency & AI-Readiness**

---

## Features

* **Semantic components** with machine-readable metadata
* **Deterministic graph identity** (semantic + configuration)
* **Contract-validated processors**
* **Typed payloads and structured context**
* **Parametric sweeps** defined in YAML
* **Modular, extensible execution layer**
* **Optional tracing with deterministic IDs**
* **HPC- and AI-ready architecture**

---

## Benefits

* **Clarity & consistency** across pipelines
* **Adaptive workflows** that evolve with domain needs
* **Scalable to HPC environments**
* **AI-driven collaboration** possible due to explicit semantics
* **Interdisciplinary communication** through shared data/operation types
* **Dynamic parameter injection** via the context stream

---

## Core Components

1. **Data Operations** — type-safe payload transformations
2. **Context Processors** — metadata and runtime parameter management
3. **Pipelines** — orchestrated execution of operations
4. **Data Types & Processor Types** — explicit semantic structures
5. **Execution Tools** — CLI, tracing, inspection utilities

---

## Pipeline Configuration & Node Factories

Pipelines are defined declaratively in **YAML**. Node factories:

* Instantiate processors
* Wire payload + context flows
* Resolve parameters
* Compute stable identities

This separation of configuration and implementation supports reproducibility and controlled evolution of workflows.

---

## License

Semantiva is released under the [Apache License 2.0](./LICENSE).

---

## Acknowledgments

Semantiva draws inspiration from the transparency and traceability requirements of large-scale scientific computing systems, notably the ALICE O² project at CERN. Lessons from managing high-throughput, HPC-oriented workflows in that environment helped shape Semantiva’s focus on typed workflows, semantic clarity, provenance, and robust execution architecture.
