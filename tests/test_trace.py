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

import json
from pathlib import Path

import pytest

from semantiva import Payload
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType
from semantiva.pipeline import Pipeline, build_graph, compute_pipeline_id
from semantiva.trace.model import TraceDriver, SERRecord
from semantiva.trace.drivers.jsonl import JSONLTrace
from semantiva.trace._utils import context_to_kv_repr


class _CaptureTrace(TraceDriver):
    def __init__(self) -> None:
        self.start: tuple[str, str, dict, dict] | None = None
        self.end: tuple[str, dict] | None = None
        self.events: list[SERRecord] = []

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        pipeline_input: Payload | None = None,
    ) -> None:
        self.start = (pipeline_id, run_id, canonical_spec, meta)

    def on_node_event(self, event: SERRecord) -> None:
        self.events.append(event)

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        self.end = (run_id, summary)

    def flush(self) -> None: ...

    def close(self) -> None: ...


def test_graph_canonicalization_parity(tmp_path: Path) -> None:
    yaml_path = Path("tests/simple_pipeline.yaml")
    nodes = load_pipeline_from_yaml(str(yaml_path))
    g_yaml = build_graph(str(yaml_path))
    g_nodes = build_graph(nodes)
    g_pipeline = build_graph(Pipeline(nodes))
    assert g_yaml == g_nodes == g_pipeline
    pid1 = compute_pipeline_id(g_yaml)
    pid2 = compute_pipeline_id(g_nodes)
    pid3 = compute_pipeline_id(g_pipeline)
    assert pid1 == pid2 == pid3


def test_trace_records_one_per_node(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    tracer = _CaptureTrace()
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    assert tracer.start is not None and tracer.end is not None
    assert len(tracer.events) == len(tracer.start[2]["nodes"])
    # Ensure each record has required fields
    for rec in tracer.events:
        assert rec.type == "ser"
        assert rec.ids["run_id"] == tracer.start[1]
        assert "node_id" in rec.ids


def test_jsonl_driver_creates_files(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    tracer1 = JSONLTrace(str(tmp_path))
    pipeline1 = Pipeline(nodes, trace=tracer1)
    pipeline1.process()
    tracer1.close()
    tracer2 = JSONLTrace(str(tmp_path))
    pipeline2 = Pipeline(nodes, trace=tracer2)
    pipeline2.process()
    tracer2.close()
    files = list(tmp_path.glob("*.ser.jsonl"))
    assert len(files) == 2
    content = [json.loads(line) for line in files[0].read_text().splitlines() if line]
    assert any(rec.get("type") == "ser" for rec in content)


def test_context_to_kv_repr() -> None:
    assert context_to_kv_repr({"b": 2, "a": 1}) == "a=1, b=2"
    big = {str(i): i for i in range(60)}
    s = context_to_kv_repr(big, max_pairs=3)
    assert s.endswith("…")
    assert s.count("=") == 3


def _run_and_load(tmp_path: Path) -> list[dict]:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()
    text = trace_path.read_text().splitlines()
    return [json.loads(ch) for ch in text if ch.strip()]


def test_output_format(tmp_path: Path) -> None:
    records = _run_and_load(tmp_path)
    assert records[0]["type"] == "pipeline_start"
    assert records[0]["schema_version"] == 0
    ser = next(
        r for r in records if r["type"] == "ser" and "factor" in r["action"]["params"]
    )
    assert ser["status"] == "completed"
    assert "cpu_ms" in ser["timing"] and ser["timing"]["cpu_ms"] >= 0
    assert "input_data" in ser.get("summaries", {})
    assert ser["action"]["params"]["factor"] == 2.0
    assert ser["action"]["param_source"]["factor"] == "node"


def test_detail_flags(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path), detail="hash")
    Pipeline(nodes, trace=tracer).process()
    tracer.close()
    ser = next(
        json.loads(line)
        for line in trace_path.read_text().splitlines()
        if line and json.loads(line)["type"] == "ser"
    )
    assert "sha256" in ser["summaries"]["input_data"]
    assert "repr" not in ser["summaries"]["input_data"]

    trace_path2 = tmp_path / "trace2.ser.jsonl"
    tracer2 = JSONLTrace(str(trace_path2), detail="repr")
    Pipeline(nodes, trace=tracer2).process()
    tracer2.close()
    ser2 = next(
        json.loads(line)
        for line in trace_path2.read_text().splitlines()
        if line and json.loads(line)["type"] == "ser"
    )
    assert "repr" in ser2["summaries"]["input_data"]
    assert "pre_context" not in ser2["summaries"] or "repr" not in ser2[
        "summaries"
    ].get("pre_context", {})

    trace_path3 = tmp_path / "trace3.ser.jsonl"
    tracer3 = JSONLTrace(str(trace_path3), detail="repr,context")
    Pipeline(nodes, trace=tracer3).process()
    tracer3.close()
    ser3 = next(
        json.loads(line)
        for line in trace_path3.read_text().splitlines()
        if line and json.loads(line)["type"] == "ser"
    )
    assert "repr" in ser3["summaries"]["input_data"]
    assert "repr" in ser3["summaries"]["pre_context"]


def test_ser_env_and_builtin_checks(tmp_path: Path) -> None:
    records = _run_and_load(tmp_path)
    ser_records = [
        r for r in records if r.get("type") == "ser" and r.get("status") == "completed"
    ]
    assert ser_records
    for rec in ser_records:
        env = rec["checks"]["why_ok"]["env"]
        assert {"python", "platform", "semantiva"}.issubset(env.keys())
        assert all(isinstance(value, (str, type(None))) for value in env.values())
        pre_checks = {entry["code"]: entry for entry in rec["checks"]["why_run"]["pre"]}
        assert "required_keys_present" in pre_checks
        assert "input_type_ok" in pre_checks
        assert isinstance(
            pre_checks["required_keys_present"]["details"].get("expected"), list
        )
    probe_record = next(
        r for r in ser_records if r["action"]["op_ref"] == "FloatBasicProbe"
    )
    post_checks = {
        entry["code"]: entry for entry in probe_record["checks"]["why_ok"]["post"]
    }
    assert "output_type_ok" in post_checks
    writes = post_checks["context_writes_realized"]["details"]
    assert "probed_data" in writes["created"]
    assert writes["missing"] == []


def test_pre_checks_detect_missing_context(tmp_path: Path) -> None:
    cfg = tmp_path / "missing_addend.yaml"
    cfg.write_text(
        """
pipeline:
  nodes:
    - processor: "FloatValueDataSource"
    - processor: "FloatAddOperation"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    with pytest.raises(KeyError):
        pipeline.process()
    tracer.close()
    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    error_ser = next(
        r for r in records if r.get("type") == "ser" and r.get("status") == "error"
    )
    pre_checks = {
        entry["code"]: entry for entry in error_ser["checks"]["why_run"]["pre"]
    }
    assert pre_checks["required_keys_present"]["result"] == "FAIL"
    assert "addend" in pre_checks["required_keys_present"]["details"]["missing"]
    assert error_ser["checks"]["why_ok"]["post"][0]["code"] == "KeyError"


def test_required_keys_satisfied_by_context(tmp_path: Path) -> None:
    cfg = tmp_path / "context_addend.yaml"
    cfg.write_text(
        """
pipeline:
  nodes:
    - processor: "FloatValueDataSource"
    - processor: "FloatAddOperation"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    payload = Payload(NoDataType(), ContextType({"addend": 3.0}))
    pipeline.process(payload)
    tracer.close()
    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    add_ser = next(
        r
        for r in records
        if r.get("type") == "ser"
        and r.get("status") == "completed"
        and r["action"]["op_ref"] == "FloatAddOperation"
    )
    pre_checks = {entry["code"]: entry for entry in add_ser["checks"]["why_run"]["pre"]}
    required = pre_checks["required_keys_present"]["details"]
    assert "addend" in required["expected"]
    assert required["missing"] == []
    assert add_ser["action"]["param_source"].get("addend") == "context"
