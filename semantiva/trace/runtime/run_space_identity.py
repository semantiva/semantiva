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

"""Compute deterministic run-space identifiers and fingerprints.

- Run-Space Configuration Format (RSCF v1) → run_space_spec_id
- Run-Space Materialization (RSM v1)       → run_space_inputs_id
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterable


@dataclass
class Fingerprint:
    """Fingerprint entry describing a run-space input."""

    role: str
    uri: str
    digest_sha256: str
    size_bytes: Optional[int] = None


@dataclass
class RunSpaceIds:
    """Computed identifiers for a run-space specification."""

    spec_id: str
    inputs_id: Optional[str]
    fingerprints: List[Fingerprint]


class RunSpaceIdentityService:
    """Computes Run-Space Configuration Format (RSCF v1) spec IDs, fingerprints,
    and optional Run-Space Materialization (RSM v1) inputs IDs.
    """

    def compute(
        self,
        run_space_spec: Dict[str, Any],
        *,
        base_dir: str | os.PathLike[str] | None = None,
    ) -> RunSpaceIds:
        """Return deterministic identifiers for ``run_space_spec``."""

        spec_bytes = self._rscf_v1(run_space_spec)
        spec_id = self._hash(b"semantiva:rscf1:", spec_bytes)

        fingerprints = self._fingerprints(run_space_spec, base_dir)
        if fingerprints:
            inputs_payload = self._rsm_v1_bytes(spec_id, fingerprints)
            inputs_id = self._hash(b"semantiva:rsm1:", inputs_payload)
        else:
            inputs_id = None
        return RunSpaceIds(
            spec_id=spec_id, inputs_id=inputs_id, fingerprints=fingerprints
        )

    # ------------------------------------------------------------------
    def _rscf_v1(self, obj: Any) -> bytes:
        def normalize(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: normalize(value[key]) for key in sorted(value)}
            if isinstance(value, list):
                return [normalize(item) for item in value]
            if isinstance(value, str):
                return value.replace("\r\n", "\n").replace("\r", "\n")
            return value

        normalized = normalize(obj)
        return json.dumps(normalized, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )

    def _fingerprints(
        self,
        spec: Dict[str, Any],
        base_dir: str | os.PathLike[str] | None,
    ) -> List[Fingerprint]:
        base = Path(base_dir) if base_dir is not None else None
        entries: List[Fingerprint] = []
        for idx, block in enumerate(spec.get("blocks", []) or []):
            if not isinstance(block, dict):
                continue
            source = block.get("source")
            if not isinstance(source, dict):
                continue
            uri, digest, size = self._fingerprint_source(source, base)
            if uri is None:
                continue
            role = source.get("role") or f"block[{idx}].source"
            entries.append(
                Fingerprint(
                    role=role,
                    uri=uri,
                    digest_sha256=digest,
                    size_bytes=size,
                )
            )
        return entries

    def _fingerprint_source(
        self,
        source: Dict[str, Any],
        base: Path | None,
    ) -> tuple[Optional[str], str, Optional[int]]:
        path = source.get("path")
        if not isinstance(path, str):
            return None, "", None
        resolved = Path(path)
        if not resolved.is_absolute() and base is not None:
            resolved = base / resolved
        resolved = resolved.expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(resolved)
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        uri = resolved.as_uri()
        digest = self._sha256_file(resolved)
        size = resolved.stat().st_size
        return uri, digest, size

    def _rsm_v1_bytes(self, spec_id: str, fps: Iterable[Fingerprint]) -> bytes:
        items = [
            {
                "role": fp.role,
                "uri": fp.uri,
                "sha256": fp.digest_sha256,
                **({"size_bytes": fp.size_bytes} if fp.size_bytes is not None else {}),
            }
            for fp in fps
        ]
        items.sort(key=lambda entry: (entry["role"], entry["uri"]))
        payload = {"spec_id": spec_id, "inputs": items}
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )

    def _sha256_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _hash(self, prefix: bytes, payload: bytes) -> str:
        digest = hashlib.sha256()
        digest.update(prefix)
        digest.update(payload)
        return digest.hexdigest()
