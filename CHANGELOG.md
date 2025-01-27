# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

