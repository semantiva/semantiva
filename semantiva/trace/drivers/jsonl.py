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

"""Simple JSONL trace driver writing Step Evidence Records (SER).

Detailed SER fields, versioning, and trace detail flags are described in
docs/source/ser.rst.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import IO, Optional, Dict
import logging

from ..model import SERRecord, TraceDriver


class JSONLTrace(TraceDriver):
    """Persist SER records to ``*.ser.jsonl`` files."""

    def __init__(
        self, output_path: str | None = None, detail: str | None = None
    ) -> None:
        self._path = Path(output_path) if output_path else Path(".")
        self._file: Optional[IO[str]] = None
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

    # TraceDriver --------------------------------------------------------------
    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        pipeline_input: Optional[object] = None,
    ) -> None:
        self._open_file(run_id)
        assert self._file is not None
        record = {
            "type": "pipeline_start",
            "schema_version": 0,
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "canonical_spec": canonical_spec,
            "meta": meta,
        }
        try:
            self._file.write(json.dumps(record, sort_keys=True) + "\n")
        except TypeError:
            logging.getLogger(__name__).warning(
                "canonical_spec not JSON serializable; omitting from trace"
            )
            record.pop("canonical_spec", None)
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
            "type": "pipeline_end",
            "schema_version": 0,
            "run_id": run_id,
            "summary": summary,
        }
        self._file.write(json.dumps(record, sort_keys=True) + "\n")

    def flush(self) -> None:
        if self._file:
            self._file.flush()

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None

    # options ---------------------------------------------------------------
    def get_options(self) -> Dict[str, bool]:
        """Return detail flag options for orchestrator.

        The mapping contains boolean flags for ``hash``, ``repr``, and
        ``context`` which control the amount of work performed to produce
        summaries in SER records.
        """

        return dict(self._opts)
