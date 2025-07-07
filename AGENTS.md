# Agent Guidelines for Semantiva

This repository houses the Semantiva framework, a dual-channel pipeline system that separates **data** from **context metadata**.

## Repository Layout

* **`semantiva/`** - Core package containing the pipeline engine and reusable components.

  * `core/` - Base classes like `SemantivaObject` for semantic metadata handling.
  * `data_types/` - Minimal data containers used throughout the framework.
  * `data_processors/` - Defines `DataOperation` and `DataProbe` along with factories for creating specialized versions.
  * `context_processors/` - Utilities for manipulating the metadata context that travels alongside data.
  * `pipeline/` - Pipeline orchestration, node definitions, and the `NodeFactory` for dynamic node creation.
  * `tools/` - Command‑line helpers such as ontology export.
  * `examples/` - Small demonstration modules and test utilities.
* **`tests/`** - Pytest suite covering the various processors, nodes, and pipeline behaviours.
* `CHANGELOG.md` and `README.md` - project history and overview

## Architecture Overview

A Semantiva pipeline processes objects called **Payloads**. Each payload contains domain data and a mutable **ContextType** mapping for metadata. The pipeline system revolves around **data processors** (operations or probes) and **context processors**. Nodes wrap these processors, and `NodeFactory` helps create them dynamically from configuration.

Key concepts include:

1. **BaseDataProcessor** - abstract class for operations on data.
2. **DataOperation** - transforms data and may produce new data; must define `input_data_type` and `output_data_type`.
3. **DataProbe** - inspects data without altering it.
4. **ContextProcessor** - manipulates the context independently of the data channel.
5. **PipelineNode** subclasses - wrappers around processors that plug into a pipeline.  Notable nodes:
   * `DataOperationNode` and `ProbeNode` for normal data processors
   * `ContextProcessorNode` for context-only operations
   * `ContextDataProcessorNode` for applying a data processor to a value stored in context
   * `DataOperationContextInjectorProbeNode` for running a data operation and storing its result back into context while passing the original data downstream

## Working with the Codebase

- Tests rely heavily on small example processors defined in `semantiva/examples/test_utils.py`. Reviewing these utilities provides a good starting point for understanding how data and context types are used.

## Contribution Workflow

1. **Formatting and Static Analysis**
   Run the following commands from the repository root before committing:
   ```sh
   black .
   mypy semantiva/ tests/
   pytest
   ```
   All code must be formatted with Black, pass type checking, and have a green test suite.

   If any command fails, fix the reported issues and rerun the checks. Only commit code when all checks succeed.

   For significant changes, add or update tests in the `tests/` directory. Use the existing tests as examples of how to create dummy data types, operations, and probes.

2. **Documentation**
   Update `README.md` or the documentation under `docs/` if the public API changes or if new features require explanation.
   Report changes in `CHANGELOG.md` under the appropriate section.


Following these guidelines ensures that agents maintain consistency across the project and that the pipeline remains introspectable and reliable.
