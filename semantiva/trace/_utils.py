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

"""Internal utilities for trace drivers.

Centralizes helpers for safe representations, deterministic JSON, and context
formatting. These functions are not part of the public API and may change
between minor versions.
"""

from __future__ import annotations

import json
import hashlib
from typing import Any, Mapping


def safe_repr(obj: Any, maxlen: int = 200) -> str:
    """Return a truncated ``repr`` string with an ellipsis suffix.

    Attempts ``repr(obj)`` and falls back to a placeholder for
    unrepresentable objects. If the resulting string exceeds ``maxlen``
    characters, it is truncated and suffixed with ``"…"``.
    """

    try:
        s = repr(obj)
    except Exception:  # pragma: no cover - defensive
        s = f"<unreprable {type(obj).__name__}>"
    if len(s) <= maxlen:
        return s
    head = max(0, maxlen - 1)
    return s[:head] + "…"


def _bytes_from_known_interfaces(obj: Any) -> bytes | None:
    """Try to obtain bytes from known object interfaces.

    Strategies in order:
      - obj.to_bytes() → bytes
      - obj.dumps() → bytes/str (encoded as UTF-8)
      - obj.to_json() / obj.json() → str (encoded)
      - memoryview / buffer protocol → bytes

    Returns:
      bytes if a known strategy succeeds; otherwise None.

    Note:
      Internal helper; callers should fall back to ``canonical_json_bytes`` or
      ``repr``.
    """
    # Priority: to_bytes
    try:
        if hasattr(obj, "to_bytes") and callable(getattr(obj, "to_bytes")):
            b = obj.to_bytes()  # type: ignore[misc]
            if isinstance(b, (bytes, bytearray, memoryview)):
                return bytes(b)
    except Exception:
        pass
    # Next: buffer protocol
    try:
        if isinstance(obj, (bytes, bytearray, memoryview)):
            return bytes(obj)
    except Exception:
        pass
    # Next: to_json
    try:
        if hasattr(obj, "to_json") and callable(getattr(obj, "to_json")):
            j = obj.to_json()  # type: ignore[misc]
            return canonical_json_bytes(j)
    except Exception:
        pass
    return None


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize ``obj`` to canonical JSON bytes (UTF-8).

    Guarantees:
      - Deterministic key ordering (sort_keys=True) and compact separators.
      - Falls back to _json_default for non-serializable types.

    Intended use:
      - Driver-side summaries (e.g., content hashes) without heavy payload copies.
    """
    try:
        return json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=_json_default,
        ).encode("utf-8")
    except Exception:  # pragma: no cover - defensive
        # Last resort: not ideal for hashing, but better than failing
        return repr(obj).encode("utf-8")


def _json_default(o: Any):
    """Default serializer for :func:`canonical_json_bytes`.

    Supports:
      - dataclasses (as dict)
      - numpy/pandas types (basic scalars) when available
      - mapping/sequence fallbacks

    Raises:
      TypeError when object cannot be represented; callers catch and fallback to
      ``repr``.
    """
    if hasattr(o, "to_json") and callable(getattr(o, "to_json")):
        try:
            return o.to_json()
        except Exception:  # pragma: no cover - defensive
            pass
    if hasattr(o, "__dict__"):
        try:
            return o.__dict__
        except Exception:  # pragma: no cover - defensive
            pass
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def serialize(obj: Any) -> bytes:
    """Best-effort serialization to bytes for hashing.

    Tries in order:
    - to_bytes() method
    - buffer protocol (bytes/bytearray/memoryview)
    - to_json() method -> :func:`canonical_json_bytes`
    - :func:`canonical_json_bytes` directly
    - ``repr(obj).encode()`` as last resort

    Used for generating stable hashes of arbitrary Python objects.
    """
    b = _bytes_from_known_interfaces(obj)
    if b is not None:
        return b
    try:
        return canonical_json_bytes(obj)
    except Exception:  # pragma: no cover - defensive
        return repr(obj).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    """Compute sha256 hex digest prefixed with 'sha256-'.

    Returns a hash string in the format 'sha256-<hexdigest>'.
    Used for generating stable content identifiers.
    """
    h = hashlib.sha256()
    h.update(data)
    return "sha256-" + h.hexdigest()


def context_to_kv_repr(mapping: Mapping[str, object], *, max_pairs: int = 150) -> str:
    """Return a deterministic ``k=v`` comma-separated string for ``mapping``.

    Keys are sorted alphabetically for reproducible output. If more than
    ``max_pairs`` items are present the result is truncated with an ``"…"``
    suffix.
    """

    items = sorted(mapping.items(), key=lambda kv: kv[0])
    parts = [f"{k}={safe_repr(v, maxlen=9999)}" for k, v in items[:max_pairs]]
    if len(items) > max_pairs:
        parts.append("…")
    return ", ".join(parts)


def json_dumps_human(obj: object) -> str:
    """Dump ``obj`` to pretty JSON with indentation and sorted keys."""

    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
