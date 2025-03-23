# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Here is the updated changelog with the missing items included and the requested rewording.

---

## [Unreleased]

### Changed
- **Centralized context management in `ContextObserver`**
  - Consolidated context updates for `ContextType`, `ContextCollectionType`, and `ChainMap` to ensure consistency.
  - Updated `ContextCollectionType` to improve structured dictionary representations and ensure better debugging.

- **Refactored Data Slicing to Processor Level**
  - Introduced `SlicingDataProcessorFactory` to **remove slicing logic from nodes**.
  - Ensured **all slicing logic now resides at the processor level**, making data slicing transparent.
  - Refactored nodes (`nodes.py`, `io_nodes.py`) to act **only as mediators** without handling slicing directly.

- **Simplified Nodes and Pipelines**
  - Updated `Pipeline` execution logic to **strictly enforce type consistency** between nodes.

### Added

- **Expanded Unit Tests for Data Slicing & Context Injection**
  - Introduced comprehensive tests for:
    - Probe result injection scenarios (`test_slicer_node_factory.py`)
    - Correct pipeline execution with automatic slicing (`test_pipeline_and_slicing.py`)
    - Context update correctness for single and collection contexts (`test_context_management.py`)

### Removed
- **Deprecated `DataCollectionProbe` and `FeatureExtractorProbeWrapper`**

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

