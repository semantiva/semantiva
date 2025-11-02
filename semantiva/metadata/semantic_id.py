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

"""Semantic identity helpers for preprocessors and pipelines."""

from __future__ import annotations

import ast
import hashlib
import json
from typing import Any, Dict, List, Tuple, cast


_UI_ONLY_KEYS = {"preprocessor_view"}


def _strip_ui_only(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: _strip_ui_only(value)
            for key, value in obj.items()
            if key not in _UI_ONLY_KEYS
        }
    if isinstance(obj, list):
        return [_strip_ui_only(value) for value in obj]
    return obj


def _dump_ast_commutative(node: ast.AST) -> str:
    """Return a canonical AST dump treating ``+``/``*`` as commutative/associative."""

    def norm(n: ast.AST) -> ast.AST:
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mult)):
            op_type = type(n.op)
            terms: List[ast.AST] = []

            def collect(term: ast.AST) -> None:
                if isinstance(term, ast.BinOp) and isinstance(term.op, op_type):
                    collect(term.left)
                    collect(term.right)
                else:
                    terms.append(term)

            collect(n)
            normalized = [norm(t) for t in terms]
            normalized.sort(key=lambda t: ast.dump(t, include_attributes=False))
            # mypy/AST typing: ensure left/right are typed as ast.expr
            current = cast(ast.expr, normalized[0])
            for term in normalized[1:]:
                term_expr = cast(ast.expr, term)
                current = ast.BinOp(left=current, op=op_type(), right=term_expr)
            return current

        for field, value in ast.iter_fields(n):
            if isinstance(value, ast.AST):
                setattr(n, field, norm(value))
            elif isinstance(value, list):
                setattr(
                    n,
                    field,
                    [
                        norm(item) if isinstance(item, ast.AST) else item
                        for item in value
                    ],
                )
        return n

    canonical = norm(ast.fix_missing_locations(node))
    return ast.dump(canonical, include_attributes=False)


def normalize_expression_sig_v1(expr: str) -> Dict[str, Any]:
    """Return ExpressionSigV1 for ``expr`` (commutative ``+``/``*`` only)."""

    tree = ast.parse(expr, mode="eval")
    return {"format": "ExpressionSigV1", "ast": _dump_ast_commutative(tree.body)}


def _sha256_json(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def variable_domain_signature(spec: Any) -> Dict[str, Any]:
    """Summarise sweep variable domains without materialising unbounded data."""

    name = type(spec).__name__
    if name == "RangeSpec":
        return {
            "kind": "range",
            "lo": float(spec.lo),
            "hi": float(spec.hi),
            "steps": int(spec.steps),
            "scale": str(getattr(spec, "scale", "linear")),
            "endpoint": bool(getattr(spec, "endpoint", True)),
        }
    if name == "SequenceSpec":
        values = list(spec.values)
        head, tail = values[:3], values[-3:]
        try:
            digest = _sha256_json(values)
        except TypeError:
            digest = hashlib.sha256(repr(values).encode("utf-8")).hexdigest()
        return {
            "kind": "sequence",
            "count": len(values),
            "sample": {"head": head, "tail": tail, "digest_sha256": digest},
        }
    if name == "FromContext":
        return {"kind": "from_context", "key": getattr(spec, "key", None)}
    return {"kind": name}


def compute_node_semantic_id(preproc_meta: Dict[str, Any]) -> str:
    """Return a deterministic fingerprint for preprocessor metadata."""

    payload = _strip_ui_only(preproc_meta)

    def _canonicalize(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _canonicalize(v) for k, v in obj.items() if k != "expr"}
        if isinstance(obj, list):
            return [_canonicalize(v) for v in obj]
        return obj

    canonical = _canonicalize(payload)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(
        f"semantiva:node-sem-v1:{payload}".encode("utf-8")
    ).hexdigest()


def compute_pipeline_config_id(pairs: List[Tuple[str, str]]) -> str:
    """Compute semantic pipeline fingerprint from ``(node_uuid, semantic_id)`` pairs."""

    ordered = sorted(pairs, key=lambda item: item[0])
    return "plcid-" + _sha256_json(ordered)


def compute_pipeline_semantic_id(canonical_spec: Dict[str, Any]) -> str:
    """Compute semantic identity for a pipeline from its canonical spec structure.

    This represents the pipeline's structure and configuration, independent of
    node implementation details. It's derived from the pipeline definition itself.
    """

    # Use the structure of nodes (names, inputs, outputs) but not runtime details
    pipeline_structure = {
        "nodes": [
            {
                "name": node.get("name"),
                "node_uuid": node.get("node_uuid"),
                "payload_from": node.get("payload_from"),
            }
            for node in canonical_spec.get("nodes", [])
        ]
    }
    payload = json.dumps(pipeline_structure, sort_keys=True, separators=(",", ":"))
    return (
        "plsemid-"
        + hashlib.sha256(
            f"semantiva:pipeline-sem-v1:{payload}".encode("utf-8")
        ).hexdigest()
    )


__all__ = [
    "compute_node_semantic_id",
    "compute_pipeline_config_id",
    "compute_pipeline_semantic_id",
    "normalize_expression_sig_v1",
    "variable_domain_signature",
]
