# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
YAML Pipeline Configuration Loader
==================================

This module provides functionality to load Semantiva pipeline configurations
from YAML files with automatic extension loading support.

YAML Structure:
--------------
```yaml
# Optional: Load extensions before parsing processors
extensions: ["semantiva_imaging"]  # or "single_package"

pipeline:
  nodes:
    - processor: "ProcessorName"
      parameters:
        param1: value1
    - processor: "delete:context_key"
    - processor: "slicer:Processor:Collection"
```

Extension Loading:
----------------------
Extensions can be specified at top-level or under pipeline section.
They are loaded before processing node definitions.

Usage:
------
```python
from semantiva.configurations import load_pipeline_from_yaml
nodes = load_pipeline_from_yaml("pipeline.yaml")
```
"""

import yaml
from typing import List, Dict, Any
from semantiva.registry import load_extensions


def load_pipeline_from_yaml(yaml_file: str) -> List[Dict[str, Any]]:
    """Load a Semantiva pipeline configuration from a YAML file.

    This function parses a YAML file containing a pipeline definition and
    automatically loads any specified extensions before returning the
    node configurations. This enables seamless integration of domain-specific
    processors and data types in pipeline definitions.

    Args:
        yaml_file: Path to the YAML file containing the pipeline configuration.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
            represents a single pipeline node configuration. Each node dict
            typically contains:
            - 'processor': The name/type of the processor to instantiate
            - 'parameters': Optional dict of parameters for the processor
            - Other node-specific configuration keys

    Raises:
        ValueError: If the YAML file is missing required structure:
                   - Missing 'pipeline' top-level key
                   - Missing 'nodes' key under 'pipeline'
                   - Invalid nested structure (non-dict objects where dicts expected)
        FileNotFoundError: If the specified YAML file cannot be found
        yaml.YAMLError: If the file contains invalid YAML syntax

    YAML Structure:
        The function expects this structure:
        ```yaml
        # Optional extensions (top-level or under pipeline)
        extensions: ["package1", "package2"] | "single_package"

        pipeline:
          nodes:
            - processor: "ProcessorName"
              parameters: {...}
            - processor: "AnotherProcessor"
        ```

    Note:
        This function only loads and returns the node configurations. It does
        not instantiate the actual Pipeline object or validate that all
        specified processors are available. Use with `Pipeline(nodes)` to
        create an executable pipeline.
    """
    with open(yaml_file, "r", encoding="utf-8") as file:
        pipeline_config = yaml.safe_load(file)

    # Load extensions if provided in YAML
    if isinstance(pipeline_config, dict):
        # Check top-level extensions first
        specs = pipeline_config.get("extensions")

        # If not found, check under pipeline section
        if not specs and isinstance(pipeline_config.get("pipeline"), dict):
            specs = pipeline_config["pipeline"].get("extensions")

        # Load extensions if any were found
        if specs:
            load_extensions(specs)

    # Validate required YAML structure
    if (
        not isinstance(pipeline_config, dict)
        or "pipeline" not in pipeline_config
        or not isinstance(pipeline_config["pipeline"], dict)
        or "nodes" not in pipeline_config["pipeline"]
    ):
        raise ValueError(
            "Invalid pipeline configuration: YAML file must contain a 'pipeline' "
            "section with a 'nodes' list. Expected structure:\n"
            "pipeline:\n  nodes:\n    - processor: 'ProcessorName'"
        )

    return pipeline_config["pipeline"]["nodes"]
