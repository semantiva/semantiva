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

Purpose
    - Persist ``pipeline_start``, ``node``, and ``pipeline_end`` envelopes to disk.
    - Low overhead: enqueue records; a background thread writes pretty JSON.

Behavior
    - Output is pretty-printed JSON (indent=2, sorted keys), separated by a blank line.
    - When ``output_path`` is a directory or None, files are auto-named as
        ``{YYYYMMDD-HHMMSS}_{RUNID}.jsonl`` within that directory.
    - Detail flags (``timings``, ``hash``, ``repr``, ``context``) control driver-side
        summaries for output data and post-execution context (hashes and readable reprs).

Resilience
    - Snapshot errors are swallowed; tracing must not break pipeline execution.
    - ``flush`` drains the queue and fsyncs; ``close`` terminates the writer thread.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, IO
import json
import logging

from .._utils import (
    safe_repr,
    serialize,
    canonical_json_bytes,
    context_to_kv_repr,
    json_dumps_human,
    sha256_bytes,
)
from semantiva.data_types import NoDataType

from ..model import NodeTraceEvent, TraceDriver


class JSONLTrace(TraceDriver):
    """Append-only JSON trace driver with background writer.

    Use ``detail`` to enable optional summaries:
      - timings (default): include t_wall/t_cpu when available
      - hash: sha256 fingerprints of output data and context
      - repr: human-friendly repr of output data
      - context: include human-friendly key→value context when combined with ``repr``
        (i.e., ``detail="repr,context"``)
    """

    _VALID_FLAGS = {"timings", "hash", "repr", "context"}

    def __init__(self, output_path: str | None = None, detail: str = "timings"):
        """Initialize driver.

        Args:
          output_path: Directory or file path. If directory/None, auto-name files per convention.
          detail: Comma-separated detail flags. Legacy single values ("timings",
            "hash", "repr", "all") are accepted for backward compatibility.
        """
        self._path = Path(output_path) if output_path else Path(".")
        self._file: Optional[IO[str]] = None
        self._queue: queue.Queue[dict | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._detail = self._parse_detail(detail)

    def _parse_detail(self, detail: str) -> set[str]:
        parts = [p.strip() for p in detail.split(",") if p.strip()]
        if not parts:
            return {"timings"}
        flags: set[str] = set()
        for p in parts:
            if p == "all":
                return {"timings", "hash", "repr", "context"}
            if p in self._VALID_FLAGS:
                flags.add(p)
        return flags or {"timings"}

    # Internal -----------------------------------------------------------------
    def _open_file(self, run_id: str) -> None:
        """Open the output file lazily on first event, using run_id for naming."""
        if self._file:
            return
        path = self._path
        if path.is_dir() or path.suffix == "":
            path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{timestamp}_{run_id}.jsonl"
            path = path / filename
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8")

    def _worker(self) -> None:
        """Background queue consumer; pretty-prints each record."""
        while True:
            item = self._queue.get()
            if item is None:
                break
            assert self._file is not None
            self._file.write(json_dumps_human(item) + "\n\n")
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
          - May emit driver-side fields: pipeline_input_repr, pipeline_input_hash.
          - Errors during snapshotting are swallowed to avoid impacting pipeline.
        """
        self._open_file(run_id)
        record = {
            "type": "pipeline_start",
            "schema_version": 1,
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "meta": meta,
        }
        try:
            json.dumps(canonical_spec)
            record["canonical_spec"] = canonical_spec
        except TypeError:
            logging.warning("canonical_spec not JSON serializable; omitting")
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
                    if "repr" in self._detail:
                        try:
                            record["pipeline_input_repr"] = safe_repr(
                                getattr(pipeline_input, "data", pipeline_input)
                            )
                        except Exception:
                            pass
                    if "hash" in self._detail:
                        try:
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
        """Write trace "node" record (before/after/error) with timings and error info.

        Output summaries (repr/hash/context) are emitted only for ``phase == 'after'``.
        """
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
                if "repr" in self._detail:
                    try:
                        record["out_data_repr"] = safe_repr(data)
                    except Exception:
                        pass
                if "hash" in self._detail:
                    try:
                        record["out_data_hash"] = sha256_bytes(serialize(data))
                    except Exception:
                        pass
            try:
                ctx = None
                if outp is not None and hasattr(outp, "context"):
                    ctx = getattr(outp, "context")
                if ctx is not None:
                    if "hash" in self._detail:
                        try:
                            ctx_view = ctx.to_dict() if hasattr(ctx, "to_dict") else ctx
                            record["post_context_hash"] = sha256_bytes(
                                canonical_json_bytes(ctx_view)
                            )
                        except Exception:
                            pass
                    if "repr" in self._detail and "context" in self._detail:
                        try:
                            ctx_view = ctx.to_dict() if hasattr(ctx, "to_dict") else ctx
                            if isinstance(ctx_view, dict):
                                record["post_context_repr"] = context_to_kv_repr(
                                    ctx_view
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
