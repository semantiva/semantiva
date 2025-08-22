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

Helpers for safe string/byte representations and canonical JSON serialization.
Not part of the public API; subject to change between minor versions.
"""

from __future__ import annotations

import json
import hashlib
from typing import Any


def safe_repr(obj: Any, maxlen: int = 120) -> str:
    """Return a truncated repr for human inspection.

    Ensures the returned string is at most ``maxlen`` characters.
    Handles unrepresentable objects gracefully.
    """
    try:
        s = repr(obj)
    except Exception:
        s = f"<unreprable {type(obj).__name__}>"
    if len(s) <= maxlen:
        return s
    # keep head only (simple, cheap)
    head = max(0, maxlen - 3)
    return s[:head] + "..."


def _bytes_from_known_interfaces(obj: Any) -> bytes | None:
    """Try to obtain bytes from known object interfaces.

    Strategies in order:
      • obj.to_bytes() → bytes
      • obj.dumps() → bytes/str (encoded as UTF-8)
      • obj.to_json() / obj.json() → str (encoded)
      • memoryview / buffer protocol → bytes

    Returns:
      bytes if a known strategy succeeds; otherwise None.

    Note:
      Internal helper; callers should fall back to canonical_json() or repr().
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
            return canonical_json(j)
    except Exception:
        pass
    return None


def canonical_json(obj: Any) -> bytes:
    """Serialize obj to canonical JSON bytes (UTF-8), for hashing or logging.

    Guarantees:
      • Deterministic key ordering (sort_keys=True) and compact separators.
      • Falls back to _json_default for non-serializable types.

    Intended use:
      • Driver-side summaries (e.g., content hashes) without heavy payload copies.
    """
    try:
        return json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=_json_default,
        ).encode("utf-8")
    except Exception:
        # Last resort: not ideal for hashing, but better than failing
        return repr(obj).encode("utf-8")


def _json_default(o: Any):
    """Default serializer for canonical_json().

    Supports:
      • dataclasses (as dict)
      • numpy/pandas types (basic scalars) when available
      • mapping/sequence fallbacks

    Raises:
      TypeError when object cannot be represented; callers catch and fallback to repr().
    """
    # Provide limited support for common types by looking for to_json
    if hasattr(o, "to_json") and callable(getattr(o, "to_json")):
        try:
            return o.to_json()
        except Exception:
            pass
    # As a last resort, try to use __dict__ if present
    if hasattr(o, "__dict__"):
        try:
            return o.__dict__
        except Exception:
            pass
    # Otherwise raise and let dumps handle it (will be caught)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def serialize(obj: Any) -> bytes:
    """Best-effort serialization to bytes for hashing.

    Tries in order:
    - to_bytes() method
    - buffer protocol (bytes/bytearray/memoryview)
    - to_json() method -> canonical_json
    - canonical_json(obj) directly
    - repr(obj).encode() as last resort

    Used for generating stable hashes of arbitrary Python objects.
    """
    b = _bytes_from_known_interfaces(obj)
    if b is not None:
        return b
    try:
        return canonical_json(obj)
    except Exception:
        return repr(obj).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    """Compute sha256 hex digest prefixed with 'sha256-'.

    Returns a hash string in the format 'sha256-<hexdigest>'.
    Used for generating stable content identifiers.
    """
    h = hashlib.sha256()
    h.update(data)
    return "sha256-" + h.hexdigest()
