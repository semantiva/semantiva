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

"""Pipeline Inspection Builder.

This module provides the core inspection data structures and builder functionality
for analyzing Semantiva pipeline configurations. The builder constructs detailed inspection
data while being resilient to configuration errors.

Key Design Principles:
- **Error Resilience**: Never raises exceptions during inspection
- **Comprehensive Data Collection**: Captures all metadata needed for analysis
- **Parameter Resolution Tracking**: Records where parameters come from
- **Context Flow Analysis**: Tracks context key lifecycle across nodes

The inspection data structures provide a single source of truth for:
- Text-based inspection reports (CLI tools)
- JSON representations (web interfaces)
- Validation and error checking
- Parameter resolution analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import inspect
from semantiva.data_processors.data_processors import ParameterInfo, _NO_DEFAULT

from semantiva.pipeline.nodes.nodes import (
    _PipelineNode,
    _ProbeContextInjectorNode,
    _ContextProcessorNode,
)
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory


@dataclass
class NodeInspection:
    """Detailed inspection data for a single pipeline node.

    This class captures all relevant information about a pipeline node including
    its configuration, parameter resolution, context interactions, and any errors
    encountered during inspection.

    Attributes:
        index: 1-based position of node in the pipeline sequence
        node_class: Name of the pipeline node wrapper class (e.g., '_DataOperationNode')
        processor_class: Name of the actual processor class (e.g., 'ImageNormalizer')
        component_type: Semantic component type from metadata (e.g., 'data_processor')
        input_type: Expected input data type (None for context-only nodes)
        output_type: Expected output data type (None for context-only nodes)
        config_params: Parameters resolved from pipeline configuration or defaults
        default_params: Parameters resolved from operation signature defaults (if not overridden by the context)
        context_params: Parameters resolved from pipeline context, with origin tracking
        created_keys: Context keys that this node adds to the pipeline context
        suppressed_keys: Context keys that this node removes from the pipeline context
        docstring: Documentation string from the processor class
        errors: List of error messages encountered during node inspection

    Parameter Resolution Tracking:
        The `context_params` dict maps parameter names to their origin node index:
        - `None` indicates the parameter comes from initial pipeline context
        - Integer value indicates the 1-based index of the node that created the key
    """

    index: int
    node_class: str
    processor_class: str
    component_type: str
    input_type: Optional[type]
    output_type: Optional[type]
    config_params: Dict[str, Any]
    default_params: Dict[str, Any]
    context_params: Dict[str, Optional[int]]
    created_keys: set[str]
    suppressed_keys: set[str]
    docstring: str
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineInspection:
    """Complete inspection results for an entire pipeline configuration.

    This class aggregates inspection data across all nodes and provides
    pipeline-level analysis including context key flow and validation results.

    Attributes:
        nodes: List of per-node inspection data in pipeline execution order
        required_context_keys: Context keys that must be provided in initial payload
        key_origin: Mapping of context keys to the node index that created them
        errors: List of pipeline-level error messages

    Context Key Flow Analysis:
        The `key_origin` dict tracks the lifecycle of context keys:
        - Keys with `None` origin must be provided in initial context
        - Keys with integer origin are created by that node (1-based index)
        - Keys may be created, used, and deleted by different nodes
    """

    nodes: List[NodeInspection]
    required_context_keys: set[str]
    key_origin: Dict[str, Optional[int]]
    errors: List[str] = field(default_factory=list)


def build_pipeline_inspection(
    node_configs: List[Dict[str, Any]],
) -> PipelineInspection:
    """
    Build a :class:`PipelineInspection` from a pipeline configuration.

    This function analyzes a raw pipeline configuration to produce detailed
    inspection results. The function is designed to be error-resilient and
    will never raise exceptions - instead, it captures error information
    within the inspection data structure.

    Args:
        node_configs: List of node configuration dictionaries

    Returns:
        PipelineInspection: Complete inspection results including per-node
            analysis, context key flow, and any errors encountered

    Error Handling:
        This function never raises exceptions. Instead, errors are captured at
        appropriate levels:
        - Pipeline-level errors go in `PipelineInspection.errors`
        - Node-level errors go in `NodeInspection.errors` for the affected node
        - Invalid nodes are still included with placeholder information

    Context Key Tracking:
        The function performs sophisticated context key flow analysis:
        1. Tracks which parameters each node requires from context
        2. Records which node created each context key (origin tracking)
        3. Handles context key deletion and validates usage after deletion
        4. Identifies external context keys required from initial payload

    Implementation Notes:
        - Attempts to construct nodes via node factory
        - Tracks parameter resolution from config vs. context sources
        - Handles special node types (probes, context processors) appropriately
        - Maintains deleted key tracking to validate parameter availability
    """

    nodes = []

    # Initialize tracking data structures
    inspection_nodes: List[NodeInspection] = []
    key_origin: Dict[str, int] = {}  # Maps context keys to the node that created them
    deleted_keys: set[str] = set()  # Tracks keys that have been deleted from context
    all_required_params: set[str] = set()  # All parameters required from context
    all_created_keys: set[str] = set()  # All keys created by any node
    errors: List[str] = []

    # Process each node configuration
    for index, node_cfg in enumerate(node_configs, start=1):
        node: Optional[_PipelineNode] = None
        node_errors: List[str] = []

        # Attempt to construct node from configuration
        try:
            node = _pipeline_node_factory(node_cfg)
            nodes.append(node)
        except Exception as exc:  # pragma: no cover - defensive
            # Node construction failed - create placeholder inspection data
            msg = str(exc)
            errors.append(f"Node {index}: {msg}")
            inspection_nodes.append(
                NodeInspection(
                    index=index,
                    node_class="Invalid",
                    processor_class=str(node_cfg.get("processor", "Unknown")),
                    component_type="Unknown",
                    input_type=None,
                    output_type=None,
                    config_params=node_cfg.get("parameters", {}),
                    default_params={},
                    context_params={},
                    created_keys=set(),
                    suppressed_keys=set(),
                    docstring="",
                    errors=[msg],
                )
            )
            continue

        # Extract node and processor information
        processor = node.processor
        metadata = node.get_metadata()

        # Analyze parameter resolution with defaults
        param_details: Dict[str, ParameterInfo] = {}
        if hasattr(processor.__class__, "_retrieve_parameter_details"):
            param_details = processor.__class__._retrieve_parameter_details(
                processor.__class__._process_logic, ["self", "data"]
            )

        config_params: Dict[str, Any] = dict(node.processor_config)
        default_params: Dict[str, Any] = {}
        context_param_names: set[str] = set()
        for name, info in param_details.items():
            if name in config_params:
                continue
            if name in key_origin and name not in deleted_keys:
                context_param_names.add(name)
                continue
            if isinstance(info, ParameterInfo) and info.default is not _NO_DEFAULT:
                config_params[name] = info.default
                default_params[name] = info.default
            else:
                context_param_names.add(name)

        # Track parameter origins for context-resolved parameters
        context_params: Dict[str, Optional[int]] = {}
        for param in context_param_names:
            # Record which node created this parameter (or None for initial context)
            context_params[param] = key_origin.get(param)

        all_required_params.update(context_param_names)

        # Analyze context key creation
        created_keys = set(node.processor.get_created_keys())

        # Special handling for probe nodes that inject results into context
        if isinstance(node, _ProbeContextInjectorNode):
            created_keys.add(node.context_keyword)
            key_origin[node.context_keyword] = index

        # Update key origin tracking for all created keys
        for key in created_keys:
            if key in deleted_keys:
                # Key is being recreated after deletion
                deleted_keys.remove(key)
            key_origin.setdefault(key, index)
        all_created_keys.update(created_keys)

        # Analyze context key suppression/deletion
        suppressed_keys = set()
        if isinstance(node, _ContextProcessorNode):
            suppressed_keys = set(node.get_suppressed_keys())
            deleted_keys.update(suppressed_keys)

            # Handle additional required keys for context processors
            if hasattr(node, "get_required_keys"):
                required = set(node.get_required_keys())
                for key in required:
                    context_params[key] = key_origin.get(key)
                all_required_params.update(required)

        # Validate parameter availability against deleted keys
        missing_deleted = (context_param_names & deleted_keys) - suppressed_keys
        if missing_deleted - set(config_params.keys()):
            node_errors.append(
                f"Node {index} requires context keys previously deleted: {sorted(missing_deleted)}"
            )

        # Create inspection data for this node
        node_inspection = NodeInspection(
            index=index,
            node_class=node.__class__.__name__,
            processor_class=processor.__class__.__name__,
            component_type=metadata.get("component_type", "Unknown"),
            input_type=getattr(node, "input_data_type", lambda: None)(),
            output_type=getattr(node, "output_data_type", lambda: None)(),
            config_params=config_params,
            default_params=default_params,
            context_params=context_params,
            created_keys=created_keys,
            suppressed_keys=suppressed_keys,
            docstring=inspect.getdoc(processor.__class__) or "No description provided.",
            errors=node_errors,
        )
        inspection_nodes.append(node_inspection)

    # Calculate pipeline-level required context keys
    # These are parameters required by nodes but not created by any node
    required_context_keys = all_required_params - all_created_keys

    return PipelineInspection(
        nodes=inspection_nodes,
        required_context_keys=required_context_keys,
        key_origin={k: v for k, v in key_origin.items()},
        errors=errors,
    )
    required_context_keys = all_required_params - all_created_keys
