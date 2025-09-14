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

"""Trace conversion utilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import IO

from semantiva.pipeline.graph_builder import compute_upstream_map


def _convert_trace_v1_to_ser_v1_1(inp: IO[str], out: IO[str]) -> None:
    canonical = None
    upstream = {}
    run_id = None
    pipeline_id = None
    for line in inp:
        if not line.strip():
            continue
        rec = json.loads(line)
        typ = rec.get("type")
        if typ == "pipeline_start":
            canonical = rec.get("canonical_spec", {})
            upstream = compute_upstream_map(canonical) if canonical else {}
            run_id = rec.get("run_id")
            pipeline_id = rec.get("pipeline_id")
            rec["schema_version"] = 2
            out.write(json.dumps(rec, sort_keys=True) + "\n")
        elif typ == "pipeline_end":
            rec["schema_version"] = 2
            out.write(json.dumps(rec, sort_keys=True) + "\n")
        elif typ == "node":
            addr = rec.get("address", {})
            node_id = addr.get("node_uuid")
            event_time = rec.get("event_time_utc")
            t_wall = rec.get("t_wall") or 0.0
            t_cpu = rec.get("t_cpu") or 0.0
            status = "error" if rec.get("phase") == "error" else "completed"
            ser = {
                "type": "ser",
                "schema_version": 2,
                "ids": {
                    "run_id": addr.get("pipeline_run_id", run_id),
                    "pipeline_id": addr.get("pipeline_id", pipeline_id),
                    "node_id": node_id,
                },
                "topology": {"upstream": upstream.get(node_id, [])},
                "action": {"op_ref": "unknown", "params": {}, "param_source": {}},
                "io_delta": {"read": [], "created": [], "updated": [], "summaries": {}},
                "checks": {
                    "why_run": {
                        "trigger": "dependency",
                        "upstream_evidence": [],
                        "pre": [],
                        "policy": [],
                    },
                    "why_ok": {
                        "post": [],
                        "invariants": [],
                        "env": {},
                        "redaction": {},
                    },
                },
                "timing": {
                    "start": event_time,
                    "end": event_time,
                    "duration_ms": int(t_wall * 1000),
                    "cpu_ms": int(t_cpu * 1000),
                },
                "status": status,
            }
            if status == "error":
                ser["error"] = {
                    "type": rec.get("error_type", "Error"),
                    "message": rec.get("error_msg", ""),
                }
            summaries = {}
            if rec.get("out_data_hash") or rec.get("out_data_repr"):
                out_s = {}
                if rec.get("out_data_hash"):
                    out_s["sha256"] = rec["out_data_hash"]
                if rec.get("out_data_repr"):
                    out_s["repr"] = rec["out_data_repr"]
                summaries["output_data"] = out_s
            if rec.get("post_context_hash") or rec.get("post_context_repr"):
                ctx_s = {}
                if rec.get("post_context_hash"):
                    ctx_s["sha256"] = rec["post_context_hash"]
                if rec.get("post_context_repr"):
                    ctx_s["repr"] = rec["post_context_repr"]
                summaries["post_context"] = ctx_s
            if summaries:
                ser["summaries"] = summaries
            out.write(json.dumps(ser, sort_keys=True) + "\n")
        else:
            out.write(line)


def convert(args) -> int:
    if args.from_format == "trace-v1" and args.to_format == "ser-v1.1":
        with Path(args.input).open("r", encoding="utf-8") as inp:
            _convert_trace_v1_to_ser_v1_1(inp, sys.stdout)
        return 0
    return 1
