# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

