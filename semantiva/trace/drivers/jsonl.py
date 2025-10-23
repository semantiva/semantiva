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

"""Simple JSONL trace driver writing Semantic Execution Records (SER).

Detailed SER fields, versioning, and trace detail flags are described in
docs/source/ser.rst.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import IO, Optional, Dict, Any
import logging

from ..model import SERRecord, TraceDriver


class JsonlTraceDriver(TraceDriver):
    """Persist SER records to ``*.ser.jsonl`` files."""

    def __init__(
        self, output_path: str | None = None, detail: str | None = None
    ) -> None:
        self._path = Path(output_path) if output_path else Path(".")
        self._file: Optional[IO[str]] = None
        self._run_space_file: Optional[IO[str]] = (
            None  # Dedicated file for run_space lifecycle
        )
        self._seq = 0
        flags = (detail or "hash").split(",")
        opts = {"hash": False, "repr": False, "context": False}
        for flag in [f.strip().lower() for f in flags]:
            if flag == "all":
                opts = {k: True for k in opts}
                break
            if flag in opts:
                opts[flag] = True
        if not any(opts.values()):
            opts["hash"] = True
        self._opts = opts

    def _now_timestamp(self) -> str:
        """Generate RFC3339 timestamp with millisecond precision and UTC 'Z'."""
        return (
            datetime.now().replace(tzinfo=None).isoformat(timespec="milliseconds") + "Z"
        )

    def _next_seq(self) -> int:
        """Return next monotonic sequence number."""
        self._seq += 1
        return self._seq

    # internal -----------------------------------------------------------------
    def _open_file(self, run_id: str) -> None:
        if self._file:
            return
        path = self._path
        if path.is_dir() or path.suffix == "":
            path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            path = path / f"{timestamp}_{run_id}.ser.jsonl"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8")

    def _open_run_space_file(self, run_space_launch_id: str) -> None:
        """Open file for run_space lifecycle events.

        Behavior depends on output_path:
        - Specific file (has extension): reuse main file handle (backward compatible)
        - Directory: create separate file with 'runspace-' prefix for clear organization
        """
        if self._run_space_file:
            return

        path = self._path

        # Single file mode: reuse the main file handle
        if path.suffix:
            if not self._file:
                self._open_file(run_space_launch_id)
            self._run_space_file = self._file
            return

        # Directory mode: create separate runspace file
        path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = path / f"{timestamp}_runspace-{run_space_launch_id}.trace.jsonl"
        self._run_space_file = path.open("a", encoding="utf-8")

    # TraceDriver --------------------------------------------------------------
    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        pipeline_spec_canonical: dict,
        meta: dict,
        pipeline_input: Optional[object] = None,
        *,
        run_space_launch_id: str | None = None,
        run_space_attempt: int | None = None,
        run_space_index: int | None = None,
        run_space_context: dict | None = None,
    ) -> None:
        self._open_file(run_id)
        assert self._file is not None
        record = {
            "record_type": "pipeline_start",
            "schema_version": 1,
            "timestamp": self._now_timestamp(),
            "seq": self._next_seq(),
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "pipeline_spec_canonical": pipeline_spec_canonical,
            "meta": meta,
        }
        if run_space_launch_id is not None:
            record["run_space_launch_id"] = run_space_launch_id
        if run_space_attempt is not None:
            record["run_space_attempt"] = run_space_attempt
        if run_space_index is not None:
            record["run_space_index"] = run_space_index
        if run_space_context is not None:
            record["run_space_context"] = run_space_context
        try:
            self._file.write(json.dumps(record, sort_keys=True) + "\n")
        except TypeError:
            logging.getLogger(__name__).warning(
                "pipeline_spec_canonical not JSON serializable; omitting from trace"
            )
            record.pop("pipeline_spec_canonical", None)
            self._file.write(json.dumps(record, sort_keys=True) + "\n")

    def on_node_event(self, event: SERRecord) -> None:
        assert self._file is not None, "trace file not open"
        # Convert dataclass to dict and remove top-level None values so the
        # emitted JSON conforms to the SER schema (which disallows null for
        # object fields like 'error').
        record = asdict(event)
        record = {k: v for k, v in record.items() if v is not None}
        try:
            self._file.write(json.dumps(record, sort_keys=True) + "\n")
        except TypeError:
            # Fall back to omitting problematic fields if serialization fails
            cleaned = {
                k: v
                for k, v in record.items()
                if isinstance(v, (str, int, float, bool, dict, list))
            }
            self._file.write(json.dumps(cleaned, sort_keys=True) + "\n")

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        if not self._file:
            return
        record = {
            "record_type": "pipeline_end",
            "schema_version": 1,
            "timestamp": self._now_timestamp(),
            "seq": self._next_seq(),
            "run_id": run_id,
            "summary": summary,
        }
        self._file.write(json.dumps(record, sort_keys=True) + "\n")

    def on_run_space_start(
        self,
        run_id: str,
        *,
        run_space_spec_id: str,
        run_space_launch_id: str,
        run_space_attempt: int,
        run_space_combine_mode: str,
        run_space_total_runs: int,
        run_space_max_runs_limit: int | None = None,
        run_space_inputs_id: str | None = None,
        run_space_input_fingerprints: list[dict[str, Any]] | None = None,
        run_space_planned_run_count: int | None = None,
    ) -> None:
        self._open_run_space_file(run_space_launch_id)
        assert self._run_space_file is not None
        record: Dict[str, Any] = {
            "record_type": "run_space_start",
            "schema_version": 1,
            "timestamp": self._now_timestamp(),
            "seq": self._next_seq(),
            "run_id": run_id,
            "run_space_spec_id": run_space_spec_id,
            "run_space_launch_id": run_space_launch_id,
            "run_space_attempt": run_space_attempt,
            "run_space_combine_mode": run_space_combine_mode,
            "run_space_total_runs": run_space_total_runs,
        }
        if run_space_max_runs_limit is not None:
            record["run_space_max_runs_limit"] = run_space_max_runs_limit
        if run_space_inputs_id is not None:
            record["run_space_inputs_id"] = run_space_inputs_id
        if run_space_input_fingerprints:
            record["run_space_input_fingerprints"] = run_space_input_fingerprints
        if run_space_planned_run_count is not None:
            record["run_space_planned_run_count"] = run_space_planned_run_count
        self._run_space_file.write(json.dumps(record, sort_keys=True) + "\n")

    def on_run_space_end(
        self,
        run_id: str,
        *,
        run_space_launch_id: str,
        run_space_attempt: int,
        summary: dict | None = None,
    ) -> None:
        self._open_run_space_file(run_space_launch_id)
        assert self._run_space_file is not None
        record = {
            "record_type": "run_space_end",
            "schema_version": 1,
            "timestamp": self._now_timestamp(),
            "seq": self._next_seq(),
            "run_id": run_id,
            "run_space_launch_id": run_space_launch_id,
            "run_space_attempt": run_space_attempt,
        }
        if summary:
            record["summary"] = summary
        self._run_space_file.write(json.dumps(record, sort_keys=True) + "\n")

    def flush(self) -> None:
        if self._file:
            self._file.flush()
        # Only flush run_space_file if it's a different handle
        if self._run_space_file and self._run_space_file is not self._file:
            self._run_space_file.flush()

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None
        # Only close run_space_file if it's a different handle
        if self._run_space_file and self._run_space_file is not self._file:
            self._run_space_file.close()
        self._run_space_file = None

    # options ---------------------------------------------------------------
    def get_options(self) -> Dict[str, bool]:
        """Return detail flag options for orchestrator.

        The mapping contains boolean flags for ``hash``, ``repr``, and
        ``context`` which control the amount of work performed to produce
        summaries in SER records.
        """

        return dict(self._opts)
