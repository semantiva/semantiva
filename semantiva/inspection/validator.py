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

"""Pipeline Inspection Validator.

This module provides validation functionality for pipeline inspection results.
The validator operates on inspection data structures rather than during pipeline
construction, allowing for validation of partially constructed or invalid pipelines.

Key Design Principles:
- **Post-inspection Validation**: Operates on inspection results, not during building
- **Error Aggregation**: Collects all errors before raising comprehensive exceptions
- **Structured Error Messages**: Provides detailed, actionable error information
- **Separation of Concerns**: Validation logic is separate from inspection building

The validator enables inspection tools to analyze invalid configurations without
failing, while still providing validation when explicitly requested.
"""

from __future__ import annotations

from typing import List

from semantiva.exceptions import PipelineConfigurationError

from .builder import PipelineInspection


def _validate_data_flow_compatibility(inspection: PipelineInspection) -> None:
    """Validate data type compatibility between consecutive nodes in the pipeline.

    This function checks that the output data type of each node is compatible
    with the input data type of the next node. Any incompatibilities are recorded
    as errors in the affected nodes.

    Args:
        inspection: Complete pipeline inspection data to validate

    Note:
        - Nodes with None input/output types are skipped (e.g., context processors)
        - Errors are added to the node that has the incompatible input type
        - Only validates consecutive data-processing nodes
    """
    for i in range(len(inspection.nodes) - 1):
        current_node = inspection.nodes[i]
        next_node = inspection.nodes[i + 1]

        # Skip validation if either node has no data types (e.g., context processors)
        if current_node.output_type is None or next_node.input_type is None:
            continue

        # Check if output type of current node matches input type of next node
        if current_node.output_type != next_node.input_type:
            error_msg = (
                f"Data type incompatibility: receives {next_node.input_type.__name__} "
                f"but previous node (Node {current_node.index}) outputs {current_node.output_type.__name__}"
            )
            next_node.errors.append(error_msg)


def validate_pipeline(inspection: PipelineInspection) -> None:
    """Raise :class:`PipelineConfigurationError` if inspection contains errors.

    This function examines the inspection results and raises a comprehensive
    exception if any errors were encountered during inspection. It aggregates
    both pipeline-level and node-level errors into a single exception message.

    Args:
        inspection: Complete pipeline inspection data to validate

    Raises:
        PipelineConfigurationError: If any errors are found in the inspection.
            The exception message contains all errors separated by semicolons,
            with node-specific errors prefixed with their node index.

    Note:
        This function is the only place in the inspection system that raises
        exceptions. The inspection builder always succeeds and records errors
        for later validation, allowing tools to inspect invalid configurations.
    """
    # Perform data flow validation first (adds errors to nodes)
    _validate_data_flow_compatibility(inspection)

    msgs: List[str] = []

    # Collect pipeline-level errors
    msgs.extend(inspection.errors)

    # Collect node-level errors with node identification
    for node in inspection.nodes:
        for err in node.errors:
            msgs.append(f"Node {node.index}: {err}")

    # Raise comprehensive exception if any errors found
    if msgs:
        raise PipelineConfigurationError("; ".join(msgs))
