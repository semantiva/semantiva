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

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Set

from ._utils import serialize, sha256_bytes, safe_repr


def _len_or_none(v: Any) -> int | None:
    try:
        return len(v)  # type: ignore[arg-type]
    except Exception:
        return None


def _rows_or_none(v: Any) -> int | None:
    try:
        # numpy/pandas-like
        if hasattr(v, "shape") and isinstance(v.shape, (list, tuple)) and v.shape:
            return int(v.shape[0])
    except Exception:
        pass
    return None


def _stable_equal(a: Any, b: Any) -> bool:
    # conservative: byte-level compare of safe serialization
    try:
        return serialize(a) == serialize(b)
    except Exception:
        return a == b


@dataclass
class IOSummary:
    dtype: str | None = None
    length: int | None = None
    rows: int | None = None
    sha256: str | None = None
    repr: str | None = None


class DeltaCollector:
    """Computes a minimal IO delta by diffing pre/post context and using declared required keys."""

    def __init__(self, *, enable_hash: bool, enable_repr: bool):
        self.enable_hash = enable_hash
        self.enable_repr = enable_repr

    def compute(
        self,
        pre_ctx: Dict[str, Any],
        post_ctx: Dict[str, Any],
        required_keys: Iterable[str] | None = None,
    ) -> dict:
        required = sorted(set(required_keys or []))

        pre_keys = set(pre_ctx.keys())
        post_keys = set(post_ctx.keys())

        created: Set[str] = post_keys - pre_keys
        maybe_updated: Set[str] = post_keys & pre_keys

        updated = sorted(
            k
            for k in maybe_updated
            if not _stable_equal(pre_ctx.get(k), post_ctx.get(k))
        )
        created_list = sorted(created)

        summaries: Dict[str, Dict[str, Any]] = {}
        # summarize only changed keys (created + updated)
        for k in sorted(created | set(updated)):
            v = post_ctx.get(k)
            rec = {
                "dtype": type(v).__name__ if v is not None else None,
                "len": _len_or_none(v),
                "rows": _rows_or_none(v),
            }
            if self.enable_hash:
                try:
                    rec["sha256"] = sha256_bytes(serialize(v))
                except Exception:
                    pass
            if self.enable_repr:
                try:
                    rec["repr"] = safe_repr(v)
                except Exception:
                    pass
            # drop Nones to keep records small
            summaries[k] = {kk: vv for kk, vv in rec.items() if vv is not None}

        return {
            "read": required,  # declared reads
            "created": created_list,  # new keys
            "updated": updated,  # changed keys
            "summaries": summaries,  # details for changed keys
        }
