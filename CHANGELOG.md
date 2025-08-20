# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Here is the updated changelog with the missing items included and the requested rewording.

---

## [Unreleased] – TBD

### Added
- **YAML Extension Integration**: Enhanced `load_pipeline_from_yaml()` with automatic extension loading
  - Accepts single extension (string) or multiple extension (list of strings)
- Enhanced extension plugin registry with improved error handling and documentation
  - Comprehensive error handling with informative warnings for missing or malformed extensions
  - Documentation of extension implementation patterns
- Enable use of data processor parameter defaults with full introspection support
- Renamed `payload_operations` → `semantiva.pipeline` and `execution_tools` → `semantiva.execution`
- Added `Payload(data: BaseDataType, context: ContextType)` in `semantiva.pipeline.payload`
- **ParametricSweepFactory**: Factory for creating parametric sweep data operations with multi-dimensional parameter ranges
- New node types  
  - `_DataOperationContextInjectorProbeNode`: runs a `DataOperation`, stores its output in the pipeline context under a specified key, and forwards the original data  
  - `_ContextDataProcessorNode`: applies a `DataOperation` or `DataProbe` to a context value and writes the result back into context  
- Factory methods
  - Exposed via `NodeFactory` to create the above node types
- Added `scripts/add_license.py` and `scripts/check_license_headers.py` for license header management
- Expanded public API exports:
  - Major expansion of `semantiva.__init__.py` to export core classes and functions including `Pipeline`, `Payload`, `load_pipeline_from_yaml`, `PipelineInspector`, data types, processors, I/O components, and workflow utilities
  - Added proper `__all__` exports to submodules: `configurations`, `core`, `exceptions`, `workflows`, and `component_loader`
  - Added package `registry` to gather plugin and class/module registry.
  - Added file `semantiva/context_processors/factory.py` for context renamer and deleter factories
  - Pluggable class name resolvers in `ClassRegistry` with built-in support for `slicer:` YAML prefixes.
- Pluggable parameter resolvers via `ClassRegistry.register_param_resolver` with built-in
    support for a ``model:`` prefix to instantiate fitting models from YAML
    pipeline definitions
- Introduced metadata and node interface contract tests to enforce component expectations

### Changed
- **Refactored Pipeline Introspection System**: Replaced `PipelineInspector` with modular inspection architecture
  - **New Inspection Module** (`semantiva.inspection`): Introduces builder/reporter/validator separation of concerns
  - **Error-Resilient Inspection**: `build_pipeline_inspection()` never raises exceptions, captures errors as inspection data instead
  - **Structured Inspection Data**: New `NodeInspection` and `PipelineInspection` dataclasses provide single source of truth
  - **Parameter Origin Tracking**: Enhanced context parameter resolution with detailed origin tracking (initial context vs. node creation)
  - **Multiple Report Formats**: Unified data drives `summary_report()`, `extended_report()`, `json_report()`, and `parameter_resolutions()`
  - **Invalid Configuration Support**: Can inspect and analyze partially valid or completely invalid pipeline configurations
  - **Post-Inspection Validation**: New `validate_pipeline()` function operates on inspection data, enabling validation as separate step
- Renamed specialization API to extension API:
  - `load_specializations()` → `load_extensions()`
  - `SemantivaSpecialization` → `SemantivaExtension`
  - Documentation, YAML key alias `extensions` replaces `specializations`
  - Test module name updated: `test_plugin_loader.py` reflects extension terminology
- Updated `PayloadSource`, `PayloadSink`, `Pipeline.process`, all node implementations, DataIO wrappers, examples and tests to use `Payload`  
- Module reorganization:
  - Moved `semantiva/tools/export_ontology.py` → `semantiva/examples/export_ontology.py` and marked as experimental
  - Renamed `semantiva/exceptions/pipeline.py` → `semantiva/exceptions/pipeline_exceptions.py`  
  - Moved `Stopwatch` class from `semantiva/utils/stopwatch.py` into `semantiva/pipeline/payload_processors.py` (deleted standalone file)
- API consolidation and public/private separation:
  - Renamed predicate mapping: `PREDICATE_MAP` → `EXPERIMENTAL_PREDICATE_MAP` with experimental disclaimers
  - Fixed global typo: `wraped_component*` → `wrapped_component*` in code, RDF export logic, and tests
- Consolidated public API by renaming classes to indicate private components by the following renames:
  - file `data_io_wrapper_factory.py` → `io_operation_factory.py`
  - file `pipeline/nodes/node_factory.py` → `_pipeline_node_factory.py`
  - file `core/semantiva_object.py` → `core/semantiva_component.py`
  - function `context_renamer_factory` → `_context_renamer_factory`
  - function `context_deleter_factory` → `_context_deleter_factory`
  - class `BaseDataProcessor` → `_BaseDataProcessor`
  - class `ContextObserver` → `_ContextObserver`
  - class `SemantivaObject` → `_SemantivaComponent`
  - class `SemantivaObjectMeta` → `_SemantivaComponentMeta`
  - class `PayloadProcessor` → `_PayloadProcessor`
  - class `SlicingDataProcessorFactory` → `_SlicingDataProcessorFactory`
  - class `DataIOWrapperFactory` → `_IOOperationFactory`
  - class `NodeFactory` → `_PipelineNodeFactory`
  - function `node_factory` → `_pipeline_node_factory`
  - class `PipelineNode` → `_PipelineNode`
  - class `DataNode` → `_DataNode`
  - class `PayloadSourceNode` → `_PayloadSourceNode`
  - class `PayloadSinkNode` → `_PayloadSinkNode`
  - class `DataSinkNode` → `_DataSinkNode`
  - class `DataSourceNode` → `_DataSourceNode`
  - class `DataOperationNode` → `_DataOperationNode`
  - class `DataOperationContextInjectorProbeNode` → `_DataOperationContextInjectorProbeNode`
  - class `ProbeNode` → `_ProbeNode`
  - class `ProbeContextInjectorNode` → `_ProbeContextInjectorNode`
  - class `ProbeResultCollectorNode` → `_ProbeResultCollectorNode`
  - class `ContextDataProcessorNode` → `_ContextDataProcessorNode`
  - class `ContextProcessorNode` → `_ContextProcessorNode`
  - Renamed `ComponentLoader` → `ClassRegistry`
  - File `Semantiva/specializations/specialization_loader.py` → `semantiva/registry/plugin_registry.py`
  - File `Semantiva/component_loader/component_loader.py` → `semantiva/registry/class_registry.py`
  - Moved `context_renamer_factory` and `context_deleter_factory` functions from `component_loader.py` to `context_processor/factory.py`

### Removed
- Deleted legacy `payload_operations/` and `execution_tools/` directories
- Deleted package `specializations/`

### Breaking Changes
- `Pipeline.process(...)` now returns `Payload` instead of a `(data, context)` tuple  
- Top-level import paths for several pipeline and execution modules have changed
- Public API consolidation: Many internal classes and functions now use underscore prefixes to indicate private status


## [v0.4.0] - 2025-06-04

### Added
- **Message-driven, pluggable execution (PR #78):**  
  - **SemantivaTransport**  
    - Defines `SemantivaTransport` (abstract) and `InMemorySemantivaTransport` for FIFO message passing between pipeline nodes.  
  - **SemantivaExecutor**  
    - Defines `SemantivaExecutor` (abstract) and `SequentialSemantivaExecutor` for synchronous task execution with `Future` compatibility.  
  - **SemantivaOrchestrator**  
    - Defines `SemantivaOrchestrator` (abstract) and `LocalSemantivaOrchestrator`, which drives a list of `PipelineNode` instances through an injected `SemantivaExecutor` and publishes every step to the chosen transport.  
  - **Pipeline refactor**  
    - `semantiva/payload_operations/pipeline.Pipeline` now accepts optional `transport` and `orchestrator` arguments.  
    - Delegates its internal `_process()` loop to `SemantivaOrchestrator.execute`, while still respecting existing timers, probes, and inspection APIs (no public API change).  
  - **Job-queue orchestration**  
    - Introduced `QueueSemantivaOrchestrator` in `semantiva/execution_tools/job_queue/queue_orchestrator.py` for FIFO job enqueue, UUID tracking, and `Future`–based result handling.  
    - Added `worker_loop()` in `semantiva/execution_tools/job_queue/worker.py` to continuously pull `jobs.*.cfg`, instantiate pipelines, process them, and publish status.  
    - Added `_setup_log()` helper in `semantiva/execution_tools/job_queue/logging_setup.py` for master/worker log files.  
- **PipelineInspector** helper class: Introduced `semantiva.tools.pipeline_inspector.PipelineInspector` to surface context parameters and semantic IDs for each node in a pipeline.  
- **ContextProcessor & Metadata refactor** (#73):  
  - Replaced `ContextNode` with dynamically generated `ContextProcessorNode` via `NodeFactory` for improved encapsulation.  
  - Made `ContextProcessor` classmethods define required keys and created keys for cleaner introspection.  
  - Injected auto-generated docstrings in `context_renamer_factory` and `context_deleter_factory`.  
  - Refactored `data_slicer_factory` to append wrapped processor docstrings to dynamically generated slicer classes.  
  - Updated `Pipeline` to support extended introspection (`extended_inspection` and `_print_nodes_semantic_ids`).  
- **SemantivaObject** as metadata foundation (#72):  
  - Added `semantiva/core/semantiva_object.py` containing the `SemantivaObject` base class for unified semantic ID and metadata handling.  
  - Refactored all relevant classes to inherit from `SemantivaObject`.  
- **Component metadata & ontology export** (#77):  
  - Introduced `SemantivaObjectMeta` and a thread-safe `_COMPONENT_REGISTRY` to register all subclasses based on their `get_metadata()`.  
  - Overrode `_define_metadata()` in `ContextObserver`, `DataSlicerFactory`, and others to ensure consistent `component_type`, I/O types, and key lists.  
  - Added `semantiva/tools/export_ontology.py`, which reads all registered component metadata and exports a complete RDF/Turtle ontology.  
  - Standardized component docstring style to one-line summaries.  
- **SlicingDataProcessorFactory** (#71):  
  - Centralized data slicing at the processor level via a new `SlicingDataProcessorFactory`.  
  - Consolidated context handling within `ContextObserver` to manage single contexts, `ContextCollectionType`, and `ChainMap` views.  
  - Enhanced `ContextCollectionType` for structured dictionary representations and dynamic slice contexts.  

### Changed
- **Changed license from MIT to Apache-2.0.**  
  - Updated `LICENSE` file to reflect the new license terms.
  - Added `NOTICE` file with attribution and license information.
- Refactored pipeline inspection logic to improve code clarity and maintainability.

### Fixed
- **Log directory creation**: Ensured that the log directory is created before attaching a file handler in `semantiva/logger/logger.py`.  

### Removed
- **Data slicing in nodes**: All slicing logic was removed from `semantiva/payload_operations/nodes`; data slicing is now exclusively managed by `SlicingDataProcessorFactory`.  
- **Deprecated probe classes**: Removed `DataCollectionProbe` and `FeatureExtractorProbeWrapper` from `semantiva/payload_operations/nodes`.  
- **Obsolete tests**: Deleted `tests/test_slicer_node_factory.py`.  

### Breaking Changes
- **Slicing behavior**:  
  > **BREAKING CHANGE**: Nodes no longer directly handle slicing logic; any pipeline that previously relied on node-level slicing must now be refactored to use `SlicingDataProcessorFactory`.  
- **ContextProcessor signature**: Some `ContextProcessor` subclasses now define classmethods (`get_required_keys`, `get_created_keys`), which may require updates if you extended them in custom code.  
- **Dynamic node generation**: The old `Node` factory API that returned anonymous classes without explicit metadata is gone; new consumers should use the updated `NodeFactory` methods and rely on `SemantivaObjectMeta` for registration.
- New location of `SemantivaSpecialization` require updates in specializations.

## [v0.3.0] - 2025-03-11

### Fixed
- **Fixed inconsistent user of `ContextType` methods on `ContextCollectionType`**
  - Corrected the use of `ContextType` methods on `ContextCollectionType` instances.
  - `ContextCollectionType` key getters and setters 

### Changed
- **Enchance Logger functionality**
 - Improve initialization and reconfiguration of Semantiva Logger
- **Rename software components**
  - **`ContextOperation` → `ContextProcessor`**
  - **`BaseDataOperation` → `BaseDataProcessor`**
    - **Justification:** The term **"Processor"** explicitly defines a **generic role** of handling data, whether through **analysis (non-modifying)** or **transformation (modifying)**.
  - **`DataAlgorithm` → `DataOperation`**
  - **Justification:**
    - The word **"Algorithm"** is too **broad and overloaded** across different fields.
    - **"Operation"** aligns well with mathematical and computational principles, clearly indicating that this component **modifies** data.

### Added

- **Added SemantivaSpecialization Interface**
  - Introduced dynamic plugin-based specialization loading.
  - Implemented **Dynamic Specialization Loading**: Specializations are now treated as plugins that can be registered and discovered dynamically.

- **Feature: Enable Data IO components into pipelines**
  - Allow `DataSource` and `DataSink` classes to be wrapped as pipeline steps via `DataIOWrapperFactory`.
  - Introduce `DataIOWrapperFactory` and `DataIONodeFactory` to wrap `DataSource`, `PayloadSource`, `DataSink`, and `PayloadSink` classes as pipeline nodes.
  - Convert `input_data_type` and `output_data_type` methods to `@staticmethod` in multiple classes for consistency and easier wrapping.
  - Add new node classes (`DataSourceNode`, `PayloadSourceNode`, `DataSinkNode`, `PayloadSinkNode`) to handle direct data injection, saving, and payload-based I/O within pipelines.
  - Update tests to validate the new I/O functionality in pipeline execution.

- **Added AI-Enhanced Development Potential to README.me**:
  - Added a new section in README.md that highlights Semantiva's AI-compatible co-design capabilities.
  - Describes features such as understanding workflow semantics, generating & modifying pipelines, explaining & debugging operations, and enhancing cross-domain usability.

- **Node and Pipeline Modularization**:
  - Nodes changed to wrap a single-purpose operation: `DataOperation` or `ContextOperation`.
  -   Introduced `PipelineNode` and specializations for `ContextNode` and `DataNode`.
  - Added `pipeline.py` and `nodes.py` under `payload_operations/` for better modularization.
  
- **Refactored Data Slicing Strategies & Improved Context Handling**:
  - Enhanced `_slicing_strategy` for clearer data-context separation.
  - Ensured proper aggregation of created keys in `_execute_data_collection_single_context`.
  - Enforced one-to-one mapping in `_execute_data_collection_context_collection`.
  
- **Pipeline Support for Collection Feature Extraction and Fit Workflow**:
  - Introduced a two-node pipeline workflow for feature extraction and model fitting.

- **Component Loader Module**:
  - Introduced `component_loader.py` to manage dynamic component loading.

- **YAML-Based Pipeline Loading**:
  - Implemented `load_pipeline_from_yaml.py` to facilitate pipeline configuration from YAML files.

- **Added Convenience Tools for Jupyter Notebook R&D and Debugging**:
  - Introduced `image_viewers.py`, providing tools to aid interactive visualization and debugging.
  - Viewers included in this release:
    - `ImageViewer`
    - `ImageInteractiveViewer`
    - `XYProjectionViewer`
    - `InteractiveCrossSectionViewer`
    - `ImageStackPlayer`

- **Enhanced Gaussian Fitting**:
  - Introduced `TwoDTiltedGaussianFitterProbe` with rotation-aware Gaussian fitting.
  - Improved initial parameter estimation using second-moment analysis.
  - Ensured orientation angle consistency with normalization to [0, 180] degrees.

- **Unit tests for base framework not dependent on Image specialization**
  - Added `tests/tests_utils.py` with `FloatDataType` and related classes for testing.
  - Added unit test for base data types, data io, pipeline, context operations based on `FloatDataType`


### Removed
- **Deprecated Data Collection Fit Probe**:
  - `data_collection_fit_probe.py` was removed, replaced by improved feature extraction workflows.

- **Semantiva specializations split from main repository**:
  - Image specialization moved to  `semantiva-imaging` 
  - Audio specialization moved to  `semantiva-audio`  

## [v0.2.0] - 2025-01-27

### Added
- Logging Support: Introduced a `Logger` class that wraps Python's `logging` module, allowing configurable verbosity and output redirection.
- New Feature Extraction and Fitting Probe:
  - Added `DataCollectionProbe` and `DataCollectionFeatureExtractionProbe` for improved data probing in collections.
  - Implemented `DataCollectionFeatureExtractionAndFitProbe` factory for feature extraction and model fitting.
  - Implemented `FittingModel` and `PolynomialFittingModel` to support function fitting.
  - Added `create_collection_feature_extraction_and_fit_probe` factory for dynamic feature extraction and model fitting.
- Context and Data Collection Enhancements:
  - Introduced `ContextCollectionType`, a specialized type for handling multiple `ContextType` instances.
  - Extended `DataCollectionType` to provide better handling of generic data collections.
- Pipeline Improvements:
  - Refactored `Pipeline._process()` to correctly slice `DataCollectionType` when required.
  - Added `_slicing_strategy()` to ensure compatibility between `DataCollectionType` and `ContextCollectionType`.
  - Enhanced logging for pipeline execution steps.
- New Image Processing Features:
  - Implemented `ImageNormalizerAlgorithm` for scaling pixel values within a specified range.
  - Added `ImageStackToSideBySideProjector` for concatenating image stacks horizontally.
  - Introduced `PNGImageStackSaver` for saving multi-frame image stacks as sequential PNG files.
  - Created `TwoDGaussianImageGenerator` for generating synthetic 2D Gaussian images.
- Improved Probes and Feature Extraction:
  - Introduced `BasicImageProbe` for extracting basic image statistics (mean, sum, min, max).
  - Added `TwoDGaussianFitterProbe` for fitting a 2D Gaussian function to image data.
- Mathematical Model Fitting:
  - Implemented `PolynomialFittingModel` to perform polynomial regression on extracted features.

### Changed
- Refactored Data Sequences to Collections:
  - Renamed `DataSequence` → `DataCollectionType` to reflect broader applicability.
  - Renamed `ContextSequenceType` → `ContextCollectionType` for consistency.
- Updated Data Processing API:
  - Refactored `BaseDataOperation` to include logging support.
  - Modified `AlgorithmTopologyFactory.create_algorithm()` to enforce stricter type validation.
- Enhanced Type Annotations and Compliance:
  - Fixed multiple type inconsistencies in `data_operations.py` and `context_operations.py`.
  - Improved MyPy compliance by adding explicit type hints in various modules.
- Improved Image Data Handling:
  - Modified `ImageStackDataType` to implement `DataCollectionType` instead of `DataSequence`.
  - Improved validation for `ImageDataType` and `ImageStackDataType`.

### Removed
- Deprecated `DataSequence` and `ContextSequenceType`:
  - These were replaced with `DataCollectionType` and `ContextCollectionType`, respectively.
- Removed `test_image_task.py`:
  - This test was replaced by `test_image_pipeline_and_task.py`, which offers broader coverage.


## [v0.1.1] - 2025-01-21
### Added
- Initial implementation of the project.
- `BaseDataType` initialization with polymorphism.
- Implemented internal logic for algorithms, probes, nodes and pipelines, including:
    - Node execution logic with stop-watch usage.
    - Pipeline initialization using a configuration dictionary.
    - Node sequence validation to ensure data compatibility.
    - Pipeline inspection to reveal node details.
    - Introduced `AlgorithmTopologyFactory` and a quick start example.
    - Added support for context operations:
    - Introduced probe nodes (`ProbeContextInjectorNode` and `ProbeResultCollectorNode`) and their tests.
- Introduced sample specializations for audio and images:
- CI pipeline:
    - Introduced `mypy` and added coverage reporting with `pytest`.
    - CI pipeline use `pdm` package.

### Fixed
- Consistent versioning between Github and Pypi

[v0.1.1]: https://github.com/semantiva/semantiva/releases/tag/v0.1.1

