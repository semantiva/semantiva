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

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import inspect
from semantiva.data_processors.data_processors import ParameterInfo
from semantiva.exceptions import InvalidNodeParameterError, PipelineConfigurationError

from semantiva.pipeline.nodes.nodes import (
    _PipelineNode,
    _ProbeContextInjectorNode,
    _ContextProcessorNode,
)
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.pipeline._param_resolution import (
    inspect_origin,
    classify_unknown_config_params,
)

from semantiva.metadata.semantic_id import (
    compute_node_semantic_id,
    compute_pipeline_config_id,
    compute_pipeline_semantic_id,
    normalize_expression_sig_v1,
    variable_domain_signature,
)
from semantiva.pipeline.graph_builder import build_canonical_spec
from semantiva.registry import resolve_symbol


def _format_processor_reference(processor: Any) -> str:
    """Return a fully-qualified name for a processor configuration reference."""

    if isinstance(processor, str):
        return processor
    if isinstance(processor, type):
        return f"{processor.__module__}.{processor.__name__}"
    if processor is None:
        return "Unknown"
    return f"{processor.__class__.__module__}.{processor.__class__.__name__}"


def _make_parameter_sweep_summary(pre: Dict[str, Any]) -> str:
    mode = pre.get("mode")
    var_names = sorted(pre.get("variables", {}).keys())
    collection = pre.get("collection")
    return (
        "Derived: parameter_sweep("
        f"mode={mode}, vars={var_names}, collection={collection})"
    )


def _build_preprocessor_view(
    expr_src: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not expr_src:
        return None
    return {
        "param_expressions": {name: {"expr": src} for name, src in expr_src.items()}
    }


def _fqcn(proc_cls: Any) -> str:
    if isinstance(proc_cls, type):
        return f"{proc_cls.__module__}.{proc_cls.__qualname__}"
    if isinstance(proc_cls, str):
        return proc_cls
    return "Unknown"


def _resolve_processor_classes(
    resolved_spec: Sequence[Mapping[str, Any]],
) -> List[Optional[type]]:
    classes: List[Optional[type]] = []
    for node_def in resolved_spec:
        proc = node_def.get("processor")
        if isinstance(proc, type):
            classes.append(proc)
        elif isinstance(proc, str):
            try:
                classes.append(resolve_symbol(proc))
            except Exception:  # pragma: no cover - defensive
                classes.append(None)
        else:
            classes.append(None)
    return classes


def _extract_nodes_and_run_space(
    config: Any,
) -> Tuple[List[Dict[str, Any]], Optional[Mapping[str, Any]]]:
    if isinstance(config, list):
        return [dict(node) for node in config], None
    if isinstance(config, Mapping):
        run_space = config.get("run_space")
        pipeline = config.get("pipeline")
        if isinstance(pipeline, Mapping):
            nodes = pipeline.get("nodes", [])
        else:
            nodes = config.get("nodes", [])
        if not isinstance(nodes, list):
            raise PipelineConfigurationError(
                "pipeline configuration must contain a list of nodes"
            )
        run_space_mapping = run_space if isinstance(run_space, Mapping) else None
        return [dict(node) for node in nodes], run_space_mapping
    raise PipelineConfigurationError(
        f"Unsupported pipeline configuration type: {type(config)!r}"
    )


def _normalize_run_space(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _normalize_run_space(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize_run_space(item) for item in value]
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    return value


def _compute_run_space_spec_id(run_space: Mapping[str, Any]) -> str:
    normalized = _normalize_run_space(run_space)
    payload = json.dumps(normalized, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    digest = hashlib.sha256()
    digest.update(b"semantiva:rscf1:")
    digest.update(payload)
    return digest.hexdigest()


def _build_sweep_payload(
    proc_cls: Optional[type], pre_meta: Mapping[str, Any] | None
) -> Dict[str, Any]:
    """Build sanitized sweep payload for inspection.

    This function implements the explicit sanitize→fingerprint→ID flow:
    1. Extract raw expressions and variable definitions from the processor
    2. Sanitize them using normalize_expression_sig_v1 and variable_domain_signature
    3. Return the sanitized block that will be passed to compute_node_semantic_id

    The sanitized signatures ensure deterministic identity computation without
    exposing raw expression strings in the inspection payload.
    """
    if not isinstance(pre_meta, Mapping):
        return {}
    if pre_meta.get("type") != "derive.parameter_sweep":
        return {}

    # Sanitize parameter expressions to canonical signatures
    parameters_sig: Dict[str, Any] = {}
    expr_src = getattr(proc_cls, "_expr_src", None)
    if isinstance(expr_src, Mapping):
        for name, expr in expr_src.items():
            if isinstance(expr, str):
                parameters_sig[name] = normalize_expression_sig_v1(expr)
            else:
                parameters_sig[name] = {"format": "ExpressionSigV1", "ast": repr(expr)}
    else:
        param_meta = pre_meta.get("param_expressions")
        if isinstance(param_meta, Mapping):
            for name, info in param_meta.items():
                if isinstance(info, Mapping) and "sig" in info:
                    parameters_sig[name] = info["sig"]

    # Sanitize variable domains to canonical signatures
    variables_sig: Dict[str, Any] = {}
    vars_src = getattr(proc_cls, "_vars", None)
    if isinstance(vars_src, Mapping):
        for name, spec in vars_src.items():
            try:
                variables_sig[name] = variable_domain_signature(spec)
            except Exception:  # pragma: no cover - defensive
                variables_sig[name] = {"kind": type(spec).__name__}
    else:
        vars_meta = pre_meta.get("variables")
        if isinstance(vars_meta, Mapping):
            for name, info in vars_meta.items():
                if isinstance(info, Mapping):
                    variables_sig[name] = info

    mode = getattr(proc_cls, "_mode", pre_meta.get("mode"))
    broadcast_attr = getattr(proc_cls, "_broadcast", pre_meta.get("broadcast", False))
    broadcast = bool(broadcast_attr) if broadcast_attr is not None else False
    collection_cls = getattr(proc_cls, "_collection_output", None)
    if isinstance(collection_cls, type):
        collection: Optional[str] = (
            f"{collection_cls.__module__}.{collection_cls.__qualname__}"
        )
    else:
        collection = pre_meta.get("collection")

    return {
        "derive": {
            "parameter_sweep": {
                "parameters_sig": parameters_sig,
                "variables_sig": variables_sig,
                "mode": mode,
                "broadcast": broadcast,
                "collection": collection,
            }
        }
    }


def collect_required_context_keys(inspection: "PipelineInspection") -> List[str]:
    """Collect and return a deterministic sorted list of required context keys.

    This ensures stable identity computation across inspection runs.
    """
    if inspection is None:
        return []
    keys: Iterable[str] = getattr(inspection, "required_context_keys", []) or []
    return sorted(set(keys))


def build_canonical_graph(
    config: Any,
    *,
    inspection: "PipelineInspection" | None = None,
) -> Dict[str, Any]:
    nodes, _ = _extract_nodes_and_run_space(config)
    canonical_spec, _ = build_canonical_spec(nodes)
    if inspection is None:
        inspection = build_pipeline_inspection(nodes)

    canonical_nodes: List[Dict[str, Any]] = []
    for idx, node in enumerate(canonical_spec.get("nodes", [])):
        enriched = dict(node)
        if idx < len(inspection.nodes):
            pre_meta = inspection.nodes[idx].preprocessor_metadata
            if isinstance(pre_meta, dict):
                enriched["preprocessor_metadata"] = pre_meta
        canonical_nodes.append(enriched)

    return {
        "version": canonical_spec.get("version"),
        "nodes": canonical_nodes,
        "edges": canonical_spec.get("edges", []),
    }


def build(
    config: Any,
    *,
    inspection: "PipelineInspection" | None = None,
) -> Dict[str, Any]:
    nodes, run_space = _extract_nodes_and_run_space(config)
    if inspection is None:
        inspection = build_pipeline_inspection(nodes)

    canonical_spec, resolved_spec = build_canonical_spec(nodes)
    proc_classes = _resolve_processor_classes(resolved_spec)

    payload_nodes: List[Dict[str, Any]] = []
    semantic_pairs: List[Tuple[str, str]] = []
    canonical_nodes: List[Dict[str, Any]] = []

    for idx, node in enumerate(canonical_spec.get("nodes", [])):
        node_uuid = node.get("node_uuid", "")
        proc_cls = proc_classes[idx] if idx < len(proc_classes) else None
        component_type = (
            inspection.nodes[idx].component_type
            if idx < len(inspection.nodes)
            else node.get("role", "Unknown")
        )
        fqcn = (
            _fqcn(proc_cls)
            if proc_cls is not None
            else _fqcn(node.get("processor_ref"))
        )

        pre_meta = (
            inspection.nodes[idx].preprocessor_metadata
            if idx < len(inspection.nodes)
            else None
        )
        node_semantic_id = "none"
        if isinstance(pre_meta, dict):
            try:
                node_semantic_id = compute_node_semantic_id(pre_meta)
            except Exception:  # pragma: no cover - defensive
                node_semantic_id = "error"
        sweep_payload = _build_sweep_payload(proc_cls, pre_meta)

        payload_nodes.append(
            {
                "uuid": node_uuid,
                "role": component_type,
                "fqcn": fqcn,
                "node_semantic_id": node_semantic_id,
                "preprocessor_metadata": sweep_payload,
            }
        )
        semantic_pairs.append((node_uuid, node_semantic_id))

        enriched = dict(node)
        if isinstance(pre_meta, dict):
            enriched["preprocessor_metadata"] = pre_meta
        canonical_nodes.append(enriched)

    canonical_for_identity = {
        "version": canonical_spec.get("version"),
        "nodes": canonical_nodes,
        "edges": canonical_spec.get("edges", []),
    }

    identity: Dict[str, Any] = {
        "semantic_id": compute_pipeline_semantic_id(canonical_for_identity),
        "config_id": compute_pipeline_config_id(semantic_pairs),
    }

    if run_space:
        try:
            spec_id = _compute_run_space_spec_id(run_space)
        except Exception:
            spec_id = None
        # Only emit spec_id; inputs_id is never computed at inspection time
        identity["run_space"] = {"spec_id": spec_id}
    else:
        identity["run_space"] = None

    payload = {
        "identity": identity,
        "pipeline_spec_canonical": {"nodes": payload_nodes},
        "required_context_keys": collect_required_context_keys(inspection),
    }
    return payload


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
        invalid_parameters: Issues for parameters not accepted by the processor
        is_configuration_valid: False if invalid parameters were detected
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
    invalid_parameters: List[Dict[str, Any]]
    is_configuration_valid: bool
    errors: List[str] = field(default_factory=list)
    required_external_parameters: List[str] = field(default_factory=list)
    derived_summary: Optional[str] = None
    preprocessor_metadata: Optional[Dict[str, Any]] = None
    preprocessor_view: Optional[Dict[str, Any]] = None


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
        processor_ref = node_cfg.get("processor")
        processor_fqcn = _format_processor_reference(processor_ref)

        # Attempt to construct node from configuration
        try:
            node = _pipeline_node_factory(node_cfg)
            nodes.append(node)
        except PipelineConfigurationError as exc:
            msg = str(exc)
            if msg.startswith("Probe nodes must declare context_key"):
                msg = (
                    "Probe nodes must declare context_key: missing for node "
                    f"{index} ({processor_fqcn})"
                )
            errors.append(f"Node {index}: {msg}")
            inspection_nodes.append(
                NodeInspection(
                    index=index,
                    node_class="Invalid",
                    processor_class=processor_fqcn.split(".")[-1],
                    component_type="Unknown",
                    input_type=None,
                    output_type=None,
                    config_params=node_cfg.get("parameters", {}),
                    default_params={},
                    context_params={},
                    created_keys=set(),
                    suppressed_keys=set(),
                    docstring="",
                    invalid_parameters=[],
                    is_configuration_valid=False,
                    errors=[msg],
                    required_external_parameters=[],
                )
            )
            continue
        except InvalidNodeParameterError as exc:
            msg = str(exc)
            errors.append(f"Node {index}: {msg}")
            issues = [
                {"name": k, "reason": "unknown_parameter"} for k in exc.invalid.keys()
            ]
            inspection_nodes.append(
                NodeInspection(
                    index=index,
                    node_class="Invalid",
                    processor_class=exc.processor_fqcn.split(".")[-1],
                    component_type="Unknown",
                    input_type=None,
                    output_type=None,
                    config_params=node_cfg.get("parameters", {}),
                    default_params={},
                    context_params={},
                    created_keys=set(),
                    suppressed_keys=set(),
                    docstring="",
                    invalid_parameters=issues,
                    is_configuration_valid=False,
                    errors=[msg],
                    required_external_parameters=[],
                )
            )
            continue
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
                    invalid_parameters=[],
                    is_configuration_valid=False,
                    errors=[msg],
                    required_external_parameters=[],
                )
            )
            continue

        # Extract node and processor information
        processor = node.processor

        issues = classify_unknown_config_params(
            processor_cls=processor.__class__,
            processor_config=node.processor_config,
        )

        # Analyze parameter resolution with defaults
        param_details: Dict[str, ParameterInfo] = {}
        # Use canonical metadata API (works for all component types)
        processor_metadata = processor.__class__.get_metadata()
        param_details = processor_metadata.get("parameters", {})

        # If metadata doesn't contain parameters, fall back to get_processing_parameter_names
        if not param_details:
            gppn = getattr(processor.__class__, "get_processing_parameter_names", None)
            if callable(gppn):
                # Build a minimal param_details mapping names -> unknown/default
                param_details = {
                    name: ParameterInfo(default=None, annotation="Unknown")
                    for name in gppn()
                }

        config_params: Dict[str, Any] = dict(node.processor_config)
        default_params: Dict[str, Any] = {}
        context_params: Dict[str, Optional[int]] = {}
        required_params: set[str] = set()
        for name in param_details.keys():
            origin, origin_idx, default_value = inspect_origin(
                name=name,
                processor_cls=processor.__class__,
                processor_config=node.processor_config,
                key_origin=key_origin,
                deleted_keys=deleted_keys,
            )
            if origin == "config":
                continue
            if origin == "context":
                context_params[name] = origin_idx
                required_params.add(name)
            elif origin == "default":
                config_params[name] = default_value
                default_params[name] = default_value
            elif origin == "required":
                context_params[name] = origin_idx
                required_params.add(name)

        # Merge explicit context requirements exposed by processor
        hook = getattr(processor.__class__, "get_context_requirements", None)
        if callable(hook):
            for key in hook():
                if key not in context_params:
                    context_params[key] = key_origin.get(key)
                required_params.add(key)

        all_required_params.update(required_params)

        required_external_parameters: List[str] = []
        required_hook = getattr(
            processor.__class__, "get_required_external_parameters", None
        )
        if callable(required_hook):
            seen: set[str] = set()
            for name in required_hook():
                if name not in seen:
                    required_external_parameters.append(name)
                    seen.add(name)
        else:
            gppn = getattr(processor.__class__, "get_processing_parameter_names", None)
            if callable(gppn):
                seen_params: set[str] = set()
                for name in gppn():
                    if name in required_params and name not in seen_params:
                        required_external_parameters.append(name)
                        seen_params.add(name)
            else:
                required_external_parameters = sorted(required_params)

        # Analyze context key creation
        created_keys: set[str] = set()
        get_ck = getattr(processor.__class__, "get_created_keys", None)
        if callable(get_ck):
            created_keys = set(get_ck())

        # Special handling for probe nodes that inject results into context
        if isinstance(node, _ProbeContextInjectorNode):
            if not isinstance(node.context_key, str) or not node.context_key.strip():
                node_errors.append(
                    "Probe nodes must declare context_key: missing for node "
                    f"{index} ({processor.__class__.__module__}.{processor.__class__.__name__})"
                )
            created_keys.add(node.context_key)
            key_origin[node.context_key] = index

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

        # Validate parameter availability against deleted keys
        missing_deleted = (required_params & deleted_keys) - suppressed_keys
        if missing_deleted - set(config_params.keys()):
            node_errors.append(
                f"Node {index} requires context keys previously deleted: {sorted(missing_deleted)}"
            )

        # Create inspection data for this node
        node_inspection = NodeInspection(
            index=index,
            node_class=node.__class__.__name__,
            processor_class=processor.__class__.__name__,
            component_type=processor_metadata.get("component_type", "Unknown"),
            input_type=getattr(node, "input_data_type", lambda: None)(),
            output_type=getattr(node, "output_data_type", lambda: None)(),
            config_params=config_params,
            default_params=default_params,
            context_params=context_params,
            created_keys=created_keys,
            suppressed_keys=suppressed_keys,
            docstring=inspect.getdoc(processor.__class__) or "No description provided.",
            invalid_parameters=issues,
            is_configuration_valid=(len(issues) == 0),
            errors=node_errors,
            required_external_parameters=required_external_parameters,
        )
        pre_meta = (
            processor_metadata.get("preprocessor")
            if isinstance(processor_metadata, dict)
            else None
        )
        if (
            isinstance(pre_meta, dict)
            and pre_meta.get("type") == "derive.parameter_sweep"
        ):
            node_inspection.derived_summary = _make_parameter_sweep_summary(pre_meta)
            node_inspection.preprocessor_metadata = pre_meta
            expr_src = getattr(processor.__class__, "_expr_src", None)
            if not expr_src and hasattr(node.__class__, "processor"):
                expr_src = getattr(node.__class__.processor, "_expr_src", None)
            view = _build_preprocessor_view(expr_src)
            if view:
                node_inspection.preprocessor_view = view
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
