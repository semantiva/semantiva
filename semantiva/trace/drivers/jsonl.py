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

"""Append-only JSONL trace driver (v1).

Writes "pipeline_start", "node", "pipeline_end" envelopes to a file with a
background thread. File naming follows the convention
``{YYYYMMDD-HHMMSS}_{RUNID}.jsonl`` when the configured output path is a
directory.
"""

from __future__ import annotations

import json
import queue
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, IO

from .._utils import safe_repr, serialize, canonical_json, sha256_bytes
from semantiva.data_types import NoDataType

from ..model import NodeTraceEvent, TraceDriver


class JSONLTrace(TraceDriver):
    """Append-only JSONL trace driver with background writer.

    Extras (driver-side, optional):
      • params_sig / input_summary / output_summary / pipeline_input_* fields MAY be added.
      • Consumers must ignore unknown fields per trace v1 rules.
    """

    def __init__(self, output_path: str | None = None, detail: str = "timings"):
        """Initialize driver.

        Args:
          output_path: Directory or file path. If directory/None, auto-name files per convention.
          detail: "timings" (default) - emit only trace v1 timings; future-friendly for summary levels.
        """
        self._path = Path(output_path) if output_path else Path(".")
        self._file: Optional[IO[str]] = None
        self._queue: queue.Queue[dict | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        # detail: one of timings, hash, repr, all
        self._detail = detail

    # Internal -----------------------------------------------------------------
    def _open_file(self, run_id: str) -> None:
        """Open the output file lazily on first event, using run_id for naming."""
        if self._file:
            return
        path = self._path
        if path.is_dir() or path.suffix == "":
            path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            filename = f"{timestamp}_{run_id}.jsonl"
            path = path / filename
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8")

    def _worker(self) -> None:
        """Background queue consumer; writes one JSON line per record; exits on sentinel None."""
        while True:
            item = self._queue.get()
            if item is None:
                break
            assert self._file is not None
            self._file.write(json.dumps(item) + "\n")
            self._queue.task_done()
        if self._file:
            self._file.flush()
            self._file.close()

    # TraceDriver --------------------------------------------------------------
    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Write trace "pipeline_start" record (schema_version=1).

        Accepts optional pipeline_input via args/kwargs:
          • May emit driver-side fields: pipeline_input_repr, pipeline_input_hash.
          • Errors during snapshotting are swallowed to avoid impacting pipeline.
        """
        self._open_file(run_id)
        record = {
            "type": "pipeline_start",
            "schema_version": 1,
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "canonical_spec": canonical_spec,
            "meta": meta,
            # omit plan_id when None; plan_epoch not emitted by default unless advanced plans are used
        }
        # include plan_epoch only if non-zero
        try:
            if getattr(self, "_plan_epoch", 0):
                record["plan_epoch"] = getattr(self, "_plan_epoch")
        except Exception:
            pass
        # Optional pipeline input snapshot (extract from kwargs or first arg)
        pipeline_input = None
        if "pipeline_input" in kwargs:
            pipeline_input = kwargs.get("pipeline_input")
        elif len(args) >= 1:
            pipeline_input = args[0]

        if pipeline_input is not None:
            # treat NoDataType as "no input" and omit snapshot
            try:
                if isinstance(
                    getattr(pipeline_input, "data", pipeline_input), NoDataType
                ):
                    pipeline_input = None
            except Exception:
                pass
            if pipeline_input is not None:
                try:
                    if self._detail in ("repr", "all"):
                        try:
                            record["pipeline_input_repr"] = safe_repr(
                                getattr(pipeline_input, "data", pipeline_input),
                                maxlen=120,
                            )
                        except Exception:
                            pass
                    if self._detail in ("hash", "all"):
                        try:
                            # compute hash from real serialization of the data
                            record["pipeline_input_hash"] = sha256_bytes(
                                serialize(
                                    getattr(pipeline_input, "data", pipeline_input)
                                )
                            )
                        except Exception:
                            pass
                except Exception:
                    # be resilient: do not fail tracing on snapshot errors
                    pass
        self._queue.put(record)

    def on_node_event(self, event: NodeTraceEvent) -> None:
        """Write trace "node" record (before/after/error) with timings and error info."""
        record = {
            "type": "node",
            "schema_version": 1,
            "phase": event.phase,
            "event_time_utc": event.event_time_utc,
            "address": asdict(event.address),
        }
        # include params only if provided
        if event.params:
            record["params"] = event.params
        # timings only when available (after/error)
        if event.t_wall is not None:
            record["t_wall"] = event.t_wall
        if event.t_cpu is not None:
            record["t_cpu"] = event.t_cpu
        # error fields only on errors
        if event.error_type is not None:
            record["error_type"] = event.error_type
        if event.error_msg is not None:
            record["error_msg"] = event.error_msg
        # plan fields only when set
        if event.plan_id is not None:
            record["plan_id"] = event.plan_id
        if getattr(event, "plan_epoch", None):
            record["plan_epoch"] = event.plan_epoch
        # Only emit output summaries at phase == 'after'
        if event.phase == "after":
            outp = getattr(event, "output_payload", None)
            if outp is not None:
                data = getattr(outp, "data", None)
                if self._detail in ("repr", "all"):
                    try:
                        record["out_data_repr"] = safe_repr(data, maxlen=120)
                    except Exception:
                        pass
                if self._detail in ("hash", "all"):
                    try:
                        record["out_data_hash"] = sha256_bytes(serialize(data))
                    except Exception:
                        pass
            # post-context hash if available
            try:
                ctx = None
                if outp is not None and hasattr(outp, "context"):
                    ctx = getattr(outp, "context")
                if ctx is not None and self._detail in ("hash", "all"):
                    try:
                        payload_ctx = ctx.to_dict() if hasattr(ctx, "to_dict") else ctx
                        record["post_context_hash"] = sha256_bytes(
                            canonical_json(payload_ctx)
                        )
                    except Exception:
                        # fallback try raw ctx
                        try:
                            record["post_context_hash"] = sha256_bytes(
                                canonical_json(ctx)
                            )
                        except Exception:
                            pass
            except Exception:
                pass
        self._queue.put(record)

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        """Write trace "pipeline_end" record with final summary (e.g., {"status": "ok"})."""
        record = {
            "type": "pipeline_end",
            "schema_version": 1,
            "run_id": run_id,
            "summary": summary,
            "plan_epoch": 0,
        }
        self._queue.put(record)

    def flush(self) -> None:
        """Block until queue is drained; fsync file if open."""
        self._queue.join()
        if self._file:
            try:
                self._file.flush()
            except Exception:
                pass

    def close(self) -> None:
        """Signal writer thread to exit and join it."""
        self._queue.put(None)
        self._thread.join()
