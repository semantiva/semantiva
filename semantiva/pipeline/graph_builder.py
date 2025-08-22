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

"""Pipeline graph construction utilities.

This module provides functionality for building and canonicalizing pipeline graphs.
It implements the GraphV1 canonical format used by the trace system.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from pathlib import Path
from typing import Any, List

import yaml

# Namespace used for deterministic node UUID generation
_NODE_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")


def _load_spec(pipeline_or_spec: Any) -> List[dict[str, Any]]:
    """Normalize input into a list of node specification dictionaries."""
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


def _canonical_node(defn: dict[str, Any]) -> dict[str, Any]:
    """Return canonical node mapping used to derive node_uuid.

    Canonical fields:
      • role, fqn, params (shallow), ports (declared)
    Canonicalization rules:
      • Sort mapping keys; strip whitespace/ordering artifacts; ignore cosmetic YAML noise.
    """
    role = defn.get("role") or "processor"
    processor = defn.get("processor")
    params = defn.get("parameters") or {}
    ports = defn.get("ports") or {}
    return {
        "role": role,
        "fqn": processor,
        "params": params,
        "ports": ports,
    }


def build_graph(pipeline_or_spec: Any) -> dict[str, Any]:
    """Build GraphV1 from YAML path, dict spec, or Pipeline object.

    Args:
      pipeline_or_spec: Path[str] | Mapping | Pipeline.

    Returns:
      dict: {"version": 1, "nodes": [{"node_uuid": str, ...}, ...], "edges": [{"source": str, "target": str}, ...]}

    Notes:
      • Node UUIDs are deterministic (UUIDv5) from _canonical_node JSON.
      • Edge construction is a linear chain for demo pipelines; future ODO will extend topology
        without breaking node_uuid semantics.
    """
    spec = _load_spec(pipeline_or_spec)
    nodes: List[dict[str, Any]] = []
    node_uuids: List[str] = []
    for raw in spec:
        canon = _canonical_node(raw)
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
    return {"version": 1, "nodes": nodes, "edges": edges}


def compute_pipeline_id(canonical_spec: dict[str, Any]) -> str:
    """Compute deterministic PipelineId for a GraphV1.

    Stable under cosmetic changes (whitespace, key order).
    Returns: "plid-" + sha256(canonical_spec JSON).
    """
    spec_json = json.dumps(canonical_spec, sort_keys=True, separators=(",", ":"))
    return "plid-" + hashlib.sha256(spec_json.encode("utf-8")).hexdigest()
