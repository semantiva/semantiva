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

"""Pipeline Inspection Reporters.

This module provides various reporting formats for pipeline inspection data.
All reporters consume the standardized inspection data structures from the
builder module and format them for different use cases.

Available Report Formats:
- **Summary Report**: Concise text format for quick pipeline overview
- **Extended Report**: Detailed text format with full documentation
- **JSON Report**: Structured data format for web interfaces and APIs
- **Parameter Resolutions**: Focused report on parameter origin tracking

Design Principles:
- **Single Source of Truth**: All reporters use the same inspection data
- **Format Separation**: No inspection logic in reporters, only formatting
- **Consistent Presentation**: Similar information structured consistently
- **Error Transparency**: All errors from inspection data are included

The reporters ensure that CLI tools, web interfaces, and API consumers
all receive consistent information about pipeline structure and parameters.
"""

from __future__ import annotations

import json
import sys

from typing import Iterable, Dict, Any, List, Optional, TextIO

from .builder import NodeInspection, PipelineInspection


def as_json_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return inspection payload as-is for JSON serialization."""

    return payload


def _format_required_keys(keys: Iterable[str]) -> str:
    values = list(keys)
    return ", ".join(values) if values else "none"


def _format_run_space(identity: Dict[str, Any]) -> str:
    run_space = identity.get("run_space")
    if isinstance(run_space, dict):
        spec_id = run_space.get("spec_id")
        if spec_id:
            return str(spec_id)
    return "none"


def _write(text: str, stream: TextIO) -> None:
    stream.write(text)


def _format_sweep_summary(block: Dict[str, Any]) -> List[str]:
    params = block.get("parameters_sig")
    vars_sig = block.get("variables_sig")
    mode = block.get("mode")
    broadcast = block.get("broadcast")
    collection = block.get("collection")
    lines = ["  Sweep:"]
    param_keys = sorted(params.keys()) if isinstance(params, dict) else []
    var_keys = sorted(vars_sig.keys()) if isinstance(vars_sig, dict) else []
    # Use a user-friendly label for CLI output
    lines.append(
        f"    swept_parameters: {', '.join(param_keys) if param_keys else 'none'}"
    )
    lines.append(f"    variables: {', '.join(var_keys) if var_keys else 'none'}")
    lines.append(f"    mode: {mode}")
    lines.append(f"    broadcast: {broadcast}")
    lines.append(f"    collection: {collection}")
    return lines


def print_cli_inspection(
    payload: Dict[str, Any],
    *,
    extended: bool = False,
    stream: TextIO | None = None,
) -> None:
    """Print concise or extended CLI inspection report from payload."""

    identity = payload.get("identity", {}) if isinstance(payload, dict) else {}
    semantic_id = identity.get("semantic_id", "unknown")
    config_id = identity.get("config_id", "unknown")
    required_keys = payload.get("required_context_keys")
    required_keys = required_keys if isinstance(required_keys, list) else []

    stream = stream or sys.stdout

    _write("Configuration Identity\n", stream)
    _write(f"- Semantic ID: {semantic_id}\n", stream)
    _write(f"- Config ID:   {config_id}\n", stream)
    _write(
        f"- Run-Space Config ID: {_format_run_space(identity)}\n",
        stream,
    )
    _write(
        f"Required Context Keys: {_format_required_keys(required_keys)}\n",
        stream,
    )

    if not extended:
        return

    nodes = (
        payload.get("pipeline_spec_canonical", {}).get("nodes", [])
        if isinstance(payload, dict)
        else []
    )
    if not isinstance(nodes, list) or not nodes:
        return

    _write("\nNodes:\n", stream)
    for node in nodes:
        if not isinstance(node, dict):
            continue
        _write(f"- UUID: {node.get('uuid', '')}\n", stream)
        _write(f"  Role: {node.get('role', '')}\n", stream)
        _write(f"  FQCN: {node.get('fqcn', '')}\n", stream)
        _write(
            f"  Node Semantic ID: {node.get('node_semantic_id', 'none')}\n",
            stream,
        )
        sweep = node.get("preprocessor_metadata")
        if isinstance(sweep, dict):
            derive = sweep.get("derive")
            if isinstance(derive, dict):
                block = derive.get("parameter_sweep")
                if isinstance(block, dict) and block:
                    for line in _format_sweep_summary(block):
                        _write(f"{line}\n", stream)
        _write("\n", stream)


def _format_set(values: Iterable[str]) -> str:
    """Format a collection of strings for human-readable display.

    Args:
        values: Collection of string values to format

    Returns:
        Comma-separated sorted string, or "None" if empty
    """
    return ", ".join(sorted(values)) if values else "None"


def _format_pipeline_config(
    processor_config: Dict[str, Any],
    default_params: Optional[Dict[str, Any]] = None,
) -> str:
    """Format pipeline configuration-provided parameters for display.

    Args:
        processor_config: Dictionary of parameter names to values
        default_params: Parameters that used signature defaults (excluded from output)

    Returns:
        Formatted string showing key=value pairs for pipeline config-provided params, or "None" if empty
    """
    if not processor_config:
        return "None"
    default_params = default_params or {}
    config_params = {
        k: v for k, v in processor_config.items() if k not in default_params
    }
    if not config_params:
        return "None"
    parts: List[str] = []
    for k, v in config_params.items():
        parts.append(f"{k}={v}")
    return ", ".join(parts)


def _format_default_params(default_params: Dict[str, Any]) -> str:
    """Format default parameters for display.

    Args:
        default_params: Dictionary of parameter names to default values

    Returns:
        Formatted string showing key=value pairs for defaults, or "None" if empty
    """
    if not default_params:
        return "None"
    parts: List[str] = []
    for k, v in default_params.items():
        parts.append(f"{k}={v}")
    return ", ".join(parts)


def _format_context_params(context_params: Dict[str, Optional[int]]) -> str:
    """Format context parameters with origin tracking information.

    Args:
        context_params: Map of parameter names to their origin node index
            (None indicates parameter comes from initial context)

    Returns:
        Formatted string showing parameters and their sources
    """
    if not context_params:
        return "None"
    parts: List[str] = []
    for param in sorted(context_params.keys()):
        origin = context_params[param]
        if origin is not None:
            parts.append(f"{param} (from Node {origin})")
        else:
            parts.append(f"{param} (from Initial Context)")
    return ", ".join(parts)


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return value
    return repr(value) if isinstance(value, (list, dict, tuple)) else str(value)


def _next_indent(indent: str) -> str:
    return indent + ("\t" if "\t" in indent else "    ")


def _format_variable_signature(name: str, sig: Dict[str, Any], indent: str) -> str:
    kind = sig.get("kind")
    if kind == "range":
        parts: List[str] = []
        for key in ("lo", "hi", "steps", "scale", "endpoint"):
            if key in sig:
                parts.append(f"{key}={_stringify(sig[key])}")
        joined = ", ".join(parts)
        return f"{indent}{name}: range({joined})"
    if kind == "sequence":
        count = sig.get("count")
        sample = sig.get("sample", {})
        head = sample.get("head")
        tail = sample.get("tail")
        digest = sample.get("digest_sha256")
        return (
            f"{indent}{name}: sequence(count={_stringify(count)}, "
            f"head={_stringify(head)}, tail={_stringify(tail)}, digest={digest})"
        )
    if kind == "from_context":
        sig_key = sig.get("key")
        return f"{indent}{name}: from_context(key={sig_key})"
    return f"{indent}{name}: {sig}"


def _format_parameter_lines(
    name: str,
    info: Dict[str, Any],
    indent: str,
    *,
    extended: bool,
    expr: Optional[str],
) -> List[str]:
    sig = info.get("sig")
    if extended:
        lines = [f"{indent}{name}:"]
        sig_indent = _next_indent(indent)
        lines.append(f"{sig_indent}sig: {json.dumps(sig, sort_keys=True)}")
        if expr is not None:
            lines.append(f"{sig_indent}expr: {expr}")
        return lines
    # Normal mode: show human-readable expr if available, otherwise fall back to sig
    if expr is not None:
        return [f"{indent}{name}: {expr}"]
    sig_repr = json.dumps(sig, sort_keys=True)
    return [f"{indent}{name}: sig={sig_repr}"]


def _format_preprocessor_block(
    node: NodeInspection,
    indent: str,
    *,
    extended: bool,
) -> List[str]:
    pre = getattr(node, "preprocessor_metadata", None)
    if not (isinstance(pre, dict) and pre.get("type") == "derive.parameter_sweep"):
        return []
    preview = getattr(node, "preprocessor_view", None)
    preview_map = (
        preview.get("param_expressions", {}) if isinstance(preview, dict) else {}
    )
    header_prefix = "- " if extended else ""
    lines: List[str] = [f"{indent}{header_prefix}Derived preprocessor:"]
    sub_indent = _next_indent(indent)
    if node.derived_summary:
        lines.append(f"{sub_indent}summary: {node.derived_summary}")
    lines.append(f"{sub_indent}type: {pre.get('type')}")
    version = pre.get("version")
    if version is not None:
        lines.append(f"{sub_indent}version: {version}")
    mode = pre.get("mode")
    if mode is not None:
        lines.append(f"{sub_indent}mode: {mode}")
    broadcast = pre.get("broadcast")
    if broadcast is not None:
        lines.append(f"{sub_indent}broadcast: {_stringify(broadcast)}")
    collection = pre.get("collection")
    if collection is not None:
        lines.append(f"{sub_indent}collection: {collection}")
    variables = pre.get("variables", {})
    if isinstance(variables, dict) and variables:
        lines.append(f"{sub_indent}variables:")
        var_indent = _next_indent(sub_indent)
        for name, sig in variables.items():
            if isinstance(sig, dict):
                lines.append(_format_variable_signature(name, sig, var_indent))
            else:
                lines.append(f"{var_indent}{name}: {sig}")
    param_exprs = pre.get("param_expressions", {})
    if isinstance(param_exprs, dict) and param_exprs:
        lines.append(f"{sub_indent}parameters:")
        param_indent = _next_indent(sub_indent)
        for name, info in param_exprs.items():
            info_dict = info if isinstance(info, dict) else {}
            expr_preview = None
            if isinstance(preview_map, dict):
                preview_entry = preview_map.get(name, {})
                if isinstance(preview_entry, dict):
                    expr_preview = preview_entry.get("expr")
            lines.extend(
                _format_parameter_lines(
                    name,
                    info_dict,
                    param_indent,
                    extended=extended,
                    expr=expr_preview,
                )
            )
    if extended:
        dependencies = pre.get("dependencies")
        if isinstance(dependencies, dict) and dependencies:
            lines.append(f"{sub_indent}dependencies: {dependencies}")
    return lines


def summary_report(inspection: PipelineInspection) -> str:
    """Generate a concise summary report of the pipeline structure.

    This report provides a quick overview of the pipeline including:
    - Required context keys from initial payload
    - Node sequence with processor types and component classifications
    - Parameter sources (configuration vs. context)
    - Context modifications (additions and deletions)
    - Any errors encountered during inspection

    Args:
        inspection: Complete pipeline inspection data

    Returns:
        Multi-line string with formatted pipeline summary
    """
    lines: List[str] = ["Pipeline Structure:"]
    lines.append(
        f"\tRequired context keys: {_format_set(inspection.required_context_keys)}"
    )

    for node in inspection.nodes:
        # Combine all parameter names for overview
        param_names = set(node.config_params.keys()) | set(node.context_params.keys())

        lines.append(
            f"\n\t{node.index}. Node: {node.processor_class} ({node.component_type})"
        )
        lines.append(f"\t\tParameters: {_format_set(param_names)}")
        lines.append(
            f"\t\t\tFrom pipeline configuration: {_format_pipeline_config(node.config_params, node.default_params)}"
        )
        lines.append(
            f"\t\t\tFrom processor defaults: {_format_default_params(node.default_params)}"
        )
        lines.append(
            f"\t\t\tFrom context: {_format_context_params(node.context_params)}"
        )
        lines.append(f"\t\tContext additions: {_format_set(node.created_keys)}")
        lines.extend(_format_preprocessor_block(node, "\t\t", extended=False))
        lines.append(
            f"\t\tInvalid parameters: {_format_set(i['name'] for i in node.invalid_parameters)}"
        )
        lines.append(f"\t\tConfiguration valid: {node.is_configuration_valid}")

        # Show context deletions only when present
        if node.suppressed_keys:
            lines.append(
                f"\t\tContext suppressions: {_format_set(node.suppressed_keys)}"
            )

        # Include any node-level errors
        for err in node.errors:
            lines.append(f"\t\tError: {err}")

    problems: List[str] = []
    for node in inspection.nodes:
        for issue in node.invalid_parameters:
            problems.append(
                f"- node #{node.index} ({node.processor_class}): {issue['name']}"
            )
    if problems:
        lines.append("\nInvalid configuration parameters:")
        lines.extend(problems)

    return "\n".join(lines)


def extended_report(inspection: PipelineInspection) -> str:
    """Generate a detailed extended report with complete node documentation.

    This report includes everything from the summary plus:
    - Full input/output data type information
    - Complete processor documentation strings
    - Detailed node class information
    - Comprehensive footnotes section with processor descriptions

    Args:
        inspection: Complete pipeline inspection data

    Returns:
        Multi-line string with formatted extended report
    """
    return _extended_report_impl(inspection, payload=None)


def _extended_report_impl(
    inspection: PipelineInspection, payload: Dict[str, Any] | None = None
) -> str:
    """Internal implementation that can optionally use payload for enrichment."""
    lines: List[str] = ["Extended Pipeline Inspection:"]
    lines.append(
        f"\tRequired context keys: {_format_set(inspection.required_context_keys)}"
    )

    # Extract node identity info from payload if available
    node_identity_map = {}
    if payload and isinstance(payload, dict):
        nodes_list = (
            payload.get("pipeline_spec_canonical", {}).get("nodes", [])
            if isinstance(payload, dict)
            else []
        )
        for idx, node_info in enumerate(nodes_list):
            if isinstance(node_info, dict):
                node_identity_map[idx] = {
                    "uuid": node_info.get("uuid", ""),
                    "role": node_info.get("role", ""),
                    "fqcn": node_info.get("fqcn", ""),
                    "node_semantic_id": node_info.get("node_semantic_id", "none"),
                }

    # Collect unique processor documentation for footnotes
    footnotes: Dict[str, str] = {}

    for node in inspection.nodes:
        # Format data type names for display
        input_name = node.input_type.__name__ if node.input_type else "None"
        output_name = node.output_type.__name__ if node.output_type else "None"

        node_header = f"\nNode {node.index}: {node.processor_class} ({node.node_class})"
        lines.append(node_header)

        # Add identity information if available
        node_idx = node.index - 1  # Convert to 0-based
        if node_idx in node_identity_map:
            identity = node_identity_map[node_idx]
            lines.extend(
                [
                    f"    - UUID: {identity['uuid']}",
                    f"    - Role: {identity['role']}",
                    f"    - FQCN: {identity['fqcn']}",
                    f"    - Node Semantic ID: {identity['node_semantic_id']}",
                ]
            )

        lines.extend(
            [
                f"    - Component type: {node.component_type}",
                f"    - Input data type: {input_name}",
                f"    - Output data type: {output_name}",
                f"    - Parameters from pipeline configuration: {_format_pipeline_config(node.config_params, node.default_params)}",
                f"    - Parameters from processor defaults: {_format_default_params(node.default_params)}",
                f"    - Parameters from context: {_format_context_params(node.context_params)}",
                f"    - Context additions: {_format_set(node.created_keys)}",
                f"    - Context suppressions: {_format_set(node.suppressed_keys)}",
            ]
        )
        lines.extend(_format_preprocessor_block(node, "    ", extended=True))
        lines.extend(
            [
                f"    - Invalid parameters: {_format_set(i['name'] for i in node.invalid_parameters)}",
                f"    - Configuration valid: {node.is_configuration_valid}",
            ]
        )

        # Store documentation for footnotes (avoid duplicates)
        footnotes.setdefault(node.processor_class, node.docstring)

        # Include any node-level errors
        for err in node.errors:
            lines.append(f"    - Error: {err}")

    # Add footnotes section with processor documentation
    lines.append("\nFootnotes:")
    for name, doc in footnotes.items():
        lines.extend([f"[{name}]", doc, ""])

    problems: List[str] = []
    for node in inspection.nodes:
        for issue in node.invalid_parameters:
            problems.append(
                f"- node #{node.index} ({node.processor_class}): {issue['name']}"
            )
    if problems:
        lines.append("\nInvalid configuration parameters:")
        lines.extend(problems)

    return "\n".join(lines)


def json_report(inspection: PipelineInspection) -> Dict[str, Any]:
    """Generate a JSON-compatible report for web interfaces and APIs.

    This format provides all inspection data in a structured format suitable
    for programmatic consumption, web visualization, and API responses.

    Args:
        inspection: Complete pipeline inspection data

    Returns:
        Dictionary with 'nodes' and 'edges' keys containing structured data
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, int]] = []

    for node in inspection.nodes:
        # Format parameter resolution data with clear separation
        config_params = {
            k: v for k, v in node.config_params.items() if k not in node.default_params
        }
        param_resolution_from_config: Dict[str, str] = {}
        for k, v in config_params.items():
            param_resolution_from_config[k] = str(v)

        param_resolution_from_defaults: Dict[str, str] = {}
        for k, v in node.default_params.items():
            param_resolution_from_defaults[k] = str(v)

        param_resolution_from_context: Dict[str, Dict[str, Any]] = {}
        for key, origin in node.context_params.items():
            if origin is not None:
                source = f"Node {origin}"
                source_idx = origin
            else:
                source = "Initial Context"
                source_idx = -1
            param_resolution_from_context[key] = {
                "value": None,  # Actual value not available during inspection
                "source": source,
                "source_idx": source_idx,
            }

        parameter_resolution = {
            "required_params": list(
                set(node.config_params.keys()) | set(node.context_params.keys())
            ),
            "from_pipeline_config": param_resolution_from_config,
            "from_processor_defaults": param_resolution_from_defaults,
            "from_context": param_resolution_from_context,
        }

        # Format data type names (handle None gracefully)
        input_name = node.input_type.__name__ if node.input_type else None
        output_name = node.output_type.__name__ if node.output_type else None

        # Create comprehensive node information dictionary
        node_info = {
            "id": node.index,
            "label": node.processor_class,
            "component_type": node.component_type,
            "input_type": input_name,
            "output_type": output_name,
            "docstring": node.docstring,
            "parameters": node.config_params,
            "parameter_resolution": parameter_resolution,
            "created_keys": list(node.created_keys),
            "required_keys": list(set(node.context_params.keys())),
            "suppressed_keys": list(node.suppressed_keys),
            "pipelineConfigParams": list(node.config_params.keys()),
            "contextParams": list(node.context_params.keys()),
            "invalid_parameters": node.invalid_parameters,
            "is_configuration_valid": node.is_configuration_valid,
            "errors": node.errors,  # Include error information for web GUI
        }
        if node.derived_summary:
            node_info["derived_summary"] = node.derived_summary
        if node.preprocessor_metadata:
            node_info["preprocessor_metadata"] = node.preprocessor_metadata
        if node.preprocessor_view:
            node_info["preprocessor_view"] = node.preprocessor_view
        nodes.append(node_info)

        # Create edges representing pipeline flow (sequential execution)
        if node.index < len(inspection.nodes):
            edges.append({"source": node.index, "target": node.index + 1})

    # Include pipeline-level information including errors
    pipeline_info = {
        "has_errors": bool(
            inspection.errors or any(node.errors for node in inspection.nodes)
        ),
        "pipeline_errors": inspection.errors,
        "required_context_keys": list(inspection.required_context_keys),
    }

    return {"nodes": nodes, "edges": edges, "pipeline": pipeline_info}


def parameter_resolutions(inspection: PipelineInspection) -> List[Dict[str, Any]]:
    """Generate a focused report on parameter resolution and origin tracking.

    This specialized reporter focuses specifically on how parameters are
    resolved across the pipeline, which is crucial for understanding
    dependencies and context flow.

    Args:
        inspection: Complete pipeline inspection data

    Returns:
        List of parameter resolution data for each node

    Note:
        Uses 0-based node indexing for compatibility with certain APIs,
        unlike other reporters which use 1-based indexing.
    """
    result: List[Dict[str, Any]] = []

    for node in inspection.nodes:
        # Separate pipeline config-provided and default parameters
        config_params = {
            k: v for k, v in node.config_params.items() if k not in node.default_params
        }
        from_config = {k: str(v) for k, v in config_params.items()}
        from_defaults = {k: str(v) for k, v in node.default_params.items()}

        # Format context parameters with detailed origin tracking
        from_context: Dict[str, Dict[str, Any]] = {}
        for key, origin in node.context_params.items():
            if origin is not None:
                source = f"Node {origin}"
                source_idx = origin
            else:
                source = "Initial Context"
                source_idx = -1
            from_context[key] = {
                "value": None,  # Actual value not available during inspection
                "source": source,
                "source_idx": source_idx,
            }

        # Create node parameter resolution summary
        node_info = {
            "id": node.index - 1,  # Convert to 0-based indexing
            "parameter_resolution": {
                "required_params": list(
                    set(node.config_params.keys()) | set(node.context_params.keys())
                ),
                "from_pipeline_config": from_config,
                "from_processor_defaults": from_defaults,
                "from_context": from_context,
            },
        }
        result.append(node_info)

    return result
