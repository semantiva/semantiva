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
    tracer2 = JSONLTrace(str(tmp_path))
    pipeline2 = Pipeline(nodes, trace=tracer2)
    pipeline2.process()
    files = list(tmp_path.glob("*.jsonl"))
    assert len(files) == 2
    content = [json.loads(line) for line in files[0].read_text().splitlines()]
    assert all("type" in rec and rec["schema_version"] == 1 for rec in content)
