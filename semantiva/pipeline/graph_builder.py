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

"""GraphV1: build and canonicalize pipeline graphs for tracing.

What this module does
    - Parses a pipeline spec (YAML path/string, list of node dicts, or Pipeline) into
        a canonical GraphV1 mapping: {"version": 1, "nodes": [...], "edges": [...]}.
    - Produces deterministic identifiers:
            - node_uuid: UUIDv5 derived from a canonical node mapping (see _canonical_node).
            - pipeline_id: "plid-<sha256>" of the canonical graph (see compute_pipeline_id).

Stability guarantees
    - Cosmetic changes (YAML whitespace, mapping key order) do not alter identities.
    - declaration_index/subindex are included in node canonical form to disambiguate
        otherwise-identical nodes declared in different positions.

Scope
    - Edges are emitted as a simple linear chain for demo/CLI pipelines; this preserves
        UUID semantics and can be extended later without breaking IDs.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from pathlib import Path
from typing import Any, List

import yaml
from semantiva.registry import ClassRegistry
from semantiva.registry.descriptors import descriptor_to_json

# Namespace used for deterministic node UUID generation
_NODE_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")


def _load_spec(pipeline_or_spec: Any) -> List[dict[str, Any]]:
    """Normalize input into a list of node specification dictionaries.

    Accepts:
      - Pipeline-like object with ``pipeline_configuration``
      - List/Tuple of node dicts
      - YAML path or YAML content (string). Supports top-level {pipeline: {nodes: [...]}}.

    Raises:
      TypeError: When input type is not supported.
    """
    if hasattr(pipeline_or_spec, "pipeline_configuration"):
        return list(pipeline_or_spec.pipeline_configuration)
    if isinstance(pipeline_or_spec, (list, tuple)):
        return list(pipeline_or_spec)
    if isinstance(pipeline_or_spec, str):
        path = Path(pipeline_or_spec)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
        else:
            loaded = yaml.safe_load(pipeline_or_spec)
        if isinstance(loaded, dict) and "pipeline" in loaded:
            loaded = loaded["pipeline"].get("nodes", [])
        assert isinstance(loaded, list)
        return loaded
    raise TypeError(
        f"Unsupported pipeline specification type: {type(pipeline_or_spec)!r}"
    )


def _canonical_node(
    defn: dict[str, Any], declaration_index: int = 0, declaration_subindex: int = 0
) -> dict[str, Any]:
    """Return canonical node mapping used to derive node_uuid.

    Canonical fields:
        - role, fqn, params (shallow), ports (declared), declaration_index, declaration_subindex
    Canonicalization rules:
        - Sort mapping keys; strip whitespace/ordering artifacts; ignore cosmetic YAML noise.

    Note: declaration_index and declaration_subindex provide a stable positional
    discriminator so that nodes with identical configuration but different
    declaration positions receive distinct UUIDs.
    """
    role = defn.get("role") or "processor"
    processor = defn.get("processor")
    if isinstance(processor, type):
        processor = f"{processor.__module__}.{processor.__qualname__}"
    params = defn.get("parameters") or {}
    ports = defn.get("ports") or {}
    canon = {
        "role": role,
        "fqn": processor,
        "params": params,
        "ports": ports,
        "declaration_index": declaration_index,
        "declaration_subindex": declaration_subindex,
    }
    return canon


def build_canonical_spec(
    pipeline_or_spec: Any,
) -> tuple[dict[str, Any], List[dict[str, Any]]]:
    """Return canonical GraphV1 spec and resolved node descriptors.

    This function normalizes the input pipeline specification, applies any
    configuration preprocessors, resolves parameters into descriptors (never
    instantiating runtime objects), and produces a JSON-serializable canonical
    graph with stable positional identities.

    Args:
        pipeline_or_spec: YAML path, mapping, or Pipeline-like object.

    Returns:
        tuple (canonical_spec, resolved_spec):
            canonical_spec: JSON-serializable GraphV1 mapping.
            resolved_spec:  List of node configs with descriptors for later
                            instantiation.
    """
    spec = _load_spec(pipeline_or_spec)
    nodes: List[dict[str, Any]] = []
    resolved: List[dict[str, Any]] = []
    node_uuids: List[str] = []
    for declaration_index, raw in enumerate(spec):
        declaration_subindex = 0
        cfg = ClassRegistry.preprocess_node_config(dict(raw))
        params = ClassRegistry.resolve_parameters(cfg.get("parameters", {}))
        cfg["parameters"] = params
        resolved.append(cfg)
        canon = _canonical_node(cfg, declaration_index, declaration_subindex)
        canon["params"] = descriptor_to_json(params)
        node_json = json.dumps(canon, sort_keys=True, separators=(",", ":"))
        node_uuid = str(uuid.uuid5(_NODE_NAMESPACE, node_json))
        canon_with_uuid = dict(canon)
        canon_with_uuid["node_uuid"] = node_uuid
        nodes.append(canon_with_uuid)
        node_uuids.append(node_uuid)
    edges = [
        {"source": node_uuids[i], "target": node_uuids[i + 1]}
        for i in range(len(node_uuids) - 1)
    ]
    return ({"version": 1, "nodes": nodes, "edges": edges}, resolved)


def build_graph(pipeline_or_spec: Any) -> dict[str, Any]:
    canonical, _ = build_canonical_spec(pipeline_or_spec)
    return canonical


def compute_pipeline_id(canonical_spec: dict[str, Any]) -> str:
    """Compute deterministic PipelineId for a GraphV1.

    Stable under cosmetic changes (whitespace, key order).
    Returns: "plid-" + sha256(canonical_spec JSON).
    """
    spec_json = json.dumps(canonical_spec, sort_keys=True, separators=(",", ":"))
    return "plid-" + hashlib.sha256(spec_json.encode("utf-8")).hexdigest()
