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

"""Emit run-space lifecycle records with process-local idempotency."""

from __future__ import annotations

from typing import Iterable, Optional, Tuple

from semantiva.trace.model import TraceDriver

from .run_space_identity import Fingerprint


class RunSpaceTraceEmitter:
    """Emit ``run_space_start`` and ``run_space_end`` records via a trace driver."""

    def __init__(self, driver: TraceDriver | None) -> None:
        self._driver = driver
        self._seen: set[Tuple[str, int]] = set()

    def emit_start(
        self,
        *,
        run_space_spec_id: str,
        run_space_launch_id: str,
        run_space_attempt: int,
        run_space_combine_mode: str,
        run_space_total_runs: int,
        run_space_max_runs_limit: Optional[int] = None,
        run_space_inputs_id: Optional[str] = None,
        run_space_input_fingerprints: Optional[Iterable[Fingerprint]] = None,
        run_space_planned_run_count: Optional[int] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """Emit a run space start trace event with input metadata."""
        if self._driver is None:
            return
        key = (run_space_launch_id, run_space_attempt)
        if key in self._seen:
            return
        self._seen.add(key)

        fingerprints_payload = None
        if run_space_input_fingerprints:
            fingerprints_payload = [
                {
                    "role": fp.role,
                    "uri": fp.uri,
                    "digest": {"sha256": fp.digest_sha256},
                    **(
                        {"size_bytes": fp.size_bytes}
                        if fp.size_bytes is not None
                        else {}
                    ),
                }
                for fp in run_space_input_fingerprints
            ]

        self._driver.on_run_space_start(
            run_id or run_space_launch_id,
            run_space_spec_id=run_space_spec_id,
            run_space_launch_id=run_space_launch_id,
            run_space_attempt=run_space_attempt,
            run_space_combine_mode=run_space_combine_mode,
            run_space_total_runs=run_space_total_runs,
            run_space_max_runs_limit=run_space_max_runs_limit,
            run_space_inputs_id=run_space_inputs_id,
            run_space_input_fingerprints=fingerprints_payload,
            run_space_planned_run_count=run_space_planned_run_count,
        )

    def emit_end(
        self,
        *,
        run_space_launch_id: str,
        run_space_attempt: int,
        summary: Optional[dict] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """Emit a run space end trace event with summary data."""
        if self._driver is None:
            return
        self._driver.on_run_space_end(
            run_id or run_space_launch_id,
            run_space_launch_id=run_space_launch_id,
            run_space_attempt=run_space_attempt,
            summary=summary or {},
        )
