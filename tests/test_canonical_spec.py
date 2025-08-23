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

import json

from semantiva.pipeline.graph_builder import build_canonical_spec
from semantiva.registry.descriptors import ModelDescriptor
from semantiva.workflows import PolynomialFittingModel


def test_build_canonical_spec_serializable():
    canonical, _ = build_canonical_spec("tests/pipeline_model_fitting.yaml")
    json.dumps(canonical)


def test_descriptor_instantiate_equivalence():
    class_path = (
        f"{PolynomialFittingModel.__module__}.{PolynomialFittingModel.__qualname__}"
    )
    desc = ModelDescriptor(class_path, {"degree": 2})
    model = desc.instantiate()
    direct = PolynomialFittingModel(degree=2)
    assert type(model) is type(direct)
    assert model.degree == direct.degree


def test_orchestrator_two_phase_flow():
    events = []

    class RecorderTrace:
        def on_pipeline_start(self, *a, **k):
            events.append("start")

        def on_node_event(self, *a, **k):
            pass

        def on_pipeline_end(self, *a, **k):
            pass

        def flush(self):
            pass

        def close(self):
            pass

    from semantiva.execution.orchestrator.orchestrator import LocalSemantivaOrchestrator
    from semantiva.examples.test_utils import FloatDataType, FloatMultiplyOperation
    from semantiva.pipeline.payload import Payload
    from semantiva.context_processors import ContextType
    from semantiva.execution.transport import InMemorySemantivaTransport
    from semantiva.logger import Logger

    class RecordingOp(FloatMultiplyOperation):
        def __init__(self, *a, **k):
            events.append("instantiate")
            super().__init__(*a, **k)

    spec = [{"processor": RecordingOp, "parameters": {"factor": 2.0}}]
    payload = Payload(FloatDataType(1.0), ContextType())
    orch = LocalSemantivaOrchestrator()
    orch.execute(
        pipeline_spec=spec,
        payload=payload,
        transport=InMemorySemantivaTransport(),
        logger=Logger(),
        trace=RecorderTrace(),
    )
    assert events[0] == "start"
    assert events[1] == "instantiate"
    assert events.count("instantiate") == 1


def test_trace_driver_defensive_guard(tmp_path, caplog):
    from semantiva.trace.drivers.jsonl import JSONLTrace

    caplog.set_level("WARNING")
    driver = JSONLTrace(output_path=tmp_path, detail="all")
    driver.on_pipeline_start("pid", "rid", {"oops": object()}, {})
    driver.flush()
    driver.close()
    files = list(tmp_path.glob("*.jsonl"))
    assert files
    content = files[0].read_text().split("\n\n")
    record = json.loads([c for c in content if c.strip()][0])
    assert "canonical_spec" not in record
    assert any("canonical_spec" in r.message for r in caplog.records)
