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
from collections import defaultdict

from semantiva import Payload
from semantiva.configurations import load_pipeline_from_yaml
from semantiva.pipeline import Pipeline, build_graph, compute_pipeline_id
from semantiva.trace.model import TraceDriver, NodeTraceEvent
from semantiva.trace.drivers.jsonl import JSONLTrace
from semantiva.trace._utils import context_to_kv_repr


class _CaptureTrace(TraceDriver):
    def __init__(self) -> None:
        self.start: tuple[str, str, dict, dict] | None = None
        self.end: tuple[str, dict] | None = None
        self.events: list[NodeTraceEvent] = []

    def on_pipeline_start(
        self,
        pipeline_id: str,
        run_id: str,
        canonical_spec: dict,
        meta: dict,
        pipeline_input: Payload | None = None,
    ) -> None:
        # Accept optional pipeline_input parameter (backward/forward compatible)
        self.start = (pipeline_id, run_id, canonical_spec, meta)

    def on_node_event(self, event: NodeTraceEvent) -> None:
        self.events.append(event)

    def on_pipeline_end(self, run_id: str, summary: dict) -> None:
        self.end = (run_id, summary)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


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


def test_trace_events_two_per_node(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    tracer = _CaptureTrace()
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    assert tracer.start is not None and tracer.end is not None
    phases = defaultdict(list)
    for ev in tracer.events:
        phases[ev.address.node_uuid].append(ev.phase)
    for p in phases.values():
        assert p == ["before", "after"]


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
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 2
    content = [
        json.loads(chunk)
        for chunk in files[0].read_text().split("\n\n")
        if chunk.strip()
    ]
    assert all("type" in rec and rec["schema_version"] == 1 for rec in content)


def test_context_to_kv_repr() -> None:
    assert context_to_kv_repr({"b": 2, "a": 1}) == "a=1, b=2"
    big = {str(i): i for i in range(60)}
    s = context_to_kv_repr(big, max_pairs=3)
    assert s.endswith("…")
    assert s.count("=") == 3


def _run_and_load(detail: str, tmp_path: Path) -> list[dict]:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.jsonl"
    tracer = JSONLTrace(str(trace_path), detail=detail)
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()
    text = trace_path.read_text()
    return [json.loads(ch) for ch in text.split("\n\n") if ch.strip()]


def test_detail_matrix(tmp_path: Path) -> None:
    details = {
        "timings": {"hash": False, "repr": False, "context": False},
        "hash": {"hash": True, "repr": False, "context": False},
        "repr": {"hash": False, "repr": True, "context": False},
        "repr,context": {"hash": False, "repr": True, "context": True},
        "all": {"hash": True, "repr": True, "context": True},
    }
    for detail, expect in details.items():
        records = _run_and_load(detail, tmp_path / detail.replace(",", "_"))
        after = [
            r for r in records if r.get("type") == "node" and r.get("phase") == "after"
        ]
        assert after
        has_hash = any("out_data_hash" in r and "post_context_hash" in r for r in after)
        has_repr = any("out_data_repr" in r for r in after)
        has_ctx_repr = any("post_context_repr" in r for r in after)
        assert has_hash == expect["hash"]
        assert has_repr == expect["repr"]
        assert has_ctx_repr == expect["context"]


def test_pretty_output(tmp_path: Path) -> None:
    _ = _run_and_load("timings", tmp_path)
    trace_file = tmp_path / "trace.jsonl"
    text = trace_file.read_text()
    assert text.startswith("{\n")
    assert "\n\n{" in text
    first = json.loads(text.split("\n\n")[0])
    assert list(first.keys()) == sorted(first.keys())
