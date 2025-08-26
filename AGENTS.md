# Agent Guidelines for Semantiva

This repository houses the Semantiva framework, a dual-channel pipeline system that separates **data** from **context metadata**.

## Repository Layout

* **semantiva/** - Core package containing the Semantiva framework:
  * **registry/** - Dynamic registry of semantiva plugins and paths.
  * **configurations/** - Helpers to build pipelines from YAML configurations.
  * **context_processors/** - Classes that manipulate pipeline context metadata.
  * **core/** - Base classes (`_SemantivaComponent`) and semantic metadata registry.
  * **data_io/** - Abstract data and payload sources and sinks.
  * **data_processors/** - Definitions of data processors: `DataOperation`, `DataProbe`, slicers, and wrappers.
  * **data_types/** - Minimal data containers used throughout the framework.
  * **examples/** - Example processors and test utilities.
  * **exceptions/** - Custom exception classes.
  * **execution/** - Pipeline execution engine and job orchestration.
  * **logger/** - Configurable logging helpers.
  * **pipeline/** - Pipeline orchestration, node definitions, and `NodeFactory` for dynamic node creation.
  * **tools/** - Command-line utilities (e.g., ontology export, pipeline inspector).
  * **workflows/** - Predefined workflow examples (e.g., model fitting).
* **tests/** - Pytest suite covering processors, nodes, and pipeline behaviors.

## Architecture Overview

A Semantiva pipeline processes objects called **Payloads**. Each payload contains domain data and a mutable **ContextType** mapping for metadata. The pipeline system revolves around **data processors** (operations or probes) and **context processors**. Nodes wrap these processors, and `NodeFactory` helps create them dynamically from configuration.

Key concepts include:

1. **_BaseDataProcessor** - abstract class for operations on data.
2. **DataOperation** - transforms data and may produce new data; must define `input_data_type` and `output_data_type`.
3. **DataProbe** - inspects data without altering it.
4. **ContextProcessor** - manipulates the context independently of the data channel.
5. **_PipelineNode** subclasses - wrappers around processors that plug into a pipeline.  Notable nodes:
   * `_DataOperationNode` and `_ProbeNode` for normal data processors
   * `_ContextProcessorNode` for context-only operations
   * `_ContextDataProcessorNode` for applying a data processor to a value stored in context
   * `_DataOperationContextInjectorProbeNode` for running a data operation and storing its result back into context while passing the original data downstream

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

2. **Documentation (REQUIRED)**
   Every PR that touches public APIs, processors, nodes, or CLI **must** keep the documentation build green.
   - **Build locally (fail on warnings)**:
     ```sh
     export SPHINXOPTS="-W --keep-going -n"
     make -C docs clean
     make -C docs html
     ```
     The HTML output is generated in `docs/build/html`.
   - **PR checklist** (mandatory):
     - [ ] Sphinx builds without warnings
     - [ ] New/changed symbols have docstrings (module, class, methods)
     - [ ] Cross‑refs (`:py:class:`, `:py:meth:`, `:py:data:`) resolve (no nitpicky errors)
     - [ ] Tutorials/concepts updated if behavior or CLI UX changed
   - **CI**: Docs are built and must pass.

3. **Changelog**
   Report changes in `CHANGELOG.md` under the appropriate section.
