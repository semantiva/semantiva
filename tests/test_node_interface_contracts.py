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

"""
Layer 2: Interface Runtime Contract Validation (Dynamic)

Behavioral verification of node & processor instantiation and delegation (no redundant metadata assertions already covered in Layer 1).

Coverage (documented in `tests/test_node_interface_contracts.py` top-level docstring):

1. Successful instantiation of each node archetype with representative concrete processor. Reuse Float-related components defined in `test_utils.py`
2. Input/Output data type delegation runtime (calling `input_data_type()` / `output_data_type()` on node matches processor rule).
3. Processing smoke test: one payload through each executable node type:
   - DataOperationNode: returns transformed).
   - ProbeNode returns pass-through data.
   - `_ProbeContextInjectorNode` injects one element in Context with the specified context key.
   - `_ProbeResultCollectorNode` does not change Context and collects the result internally.
   - Source nodes produce data from `NoDataType` payload.
   - Sink nodes accept data without raising and pass through unchanged.
   - General guide to test nodes: use the user-friendly node definition in a dictionary to define the nodes and run a single-node pipeline for each test.
4. Error handling:
   - Type mismatch raises TypeError in `_DataNode._process`.
5. Logger handling: default logger is created when none supplied and a provided logger is preserved.
6. Context injection behavior: `_ProbeContextInjectorNode` stores the probe result under the requested key without altering unrelated context.
7. No metadata assertions here (delegated fully to Layer 1).
8. No cherry picked regression tests: previously failing patterns should already be covered by the robust test strategy outlined above.
"""

from __future__ import annotations

import pytest
from semantiva.logger import Logger
from semantiva.pipeline import Payload
from semantiva.context_processors.context_types import ContextType
from semantiva.data_types import NoDataType, BaseDataType
from semantiva.pipeline.nodes.nodes import (
    _DataSourceNode,
    _PayloadSourceNode,
    _DataSinkNode,
    _PayloadSinkNode,
    _DataOperationNode,
    _ProbeContextInjectorNode,
    _ProbeResultCollectorNode,
)
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.examples.test_utils import (
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    FloatMultiplyOperation,
    FloatBasicProbe,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_logger() -> Logger:
    return Logger(level="ERROR", console_output=False, name="test_logger")


def _make_data_source_node():
    return _pipeline_node_factory({"processor": FloatDataSource}, _make_logger())


def _make_payload_source_node():
    return _pipeline_node_factory({"processor": FloatPayloadSource}, _make_logger())


def _make_data_sink_node():
    return _pipeline_node_factory({"processor": FloatDataSink}, _make_logger())


def _make_payload_sink_node():
    return _pipeline_node_factory({"processor": FloatPayloadSink}, _make_logger())


def _make_data_operation_node():
    return _pipeline_node_factory(
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
        _make_logger(),
    )


def _make_probe_context_injector_node():
    return _pipeline_node_factory(
        {"processor": FloatBasicProbe, "context_keyword": "probe_key"},
        _make_logger(),
    )


def _make_probe_result_collector_node():
    return _pipeline_node_factory({"processor": FloatBasicProbe}, _make_logger())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory, expected_type",
    [
        (_make_data_source_node, _DataSourceNode),
        (_make_payload_source_node, _PayloadSourceNode),
        (_make_data_sink_node, _DataSinkNode),
        (_make_payload_sink_node, _PayloadSinkNode),
        (_make_data_operation_node, _DataOperationNode),
        (_make_probe_context_injector_node, _ProbeContextInjectorNode),
        (_make_probe_result_collector_node, _ProbeResultCollectorNode),
    ],
)
def test_instantiation_variants(factory, expected_type):
    node = factory()
    assert isinstance(node, expected_type)


@pytest.mark.parametrize(
    "factory, expected_in, expected_out",
    [
        (_make_data_source_node, NoDataType, FloatBasicProbe.input_data_type()),
        (_make_payload_source_node, NoDataType, FloatBasicProbe.input_data_type()),
        (
            _make_data_sink_node,
            FloatBasicProbe.input_data_type(),
            FloatBasicProbe.input_data_type(),
        ),
        (
            _make_payload_sink_node,
            FloatBasicProbe.input_data_type(),
            FloatBasicProbe.input_data_type(),
        ),
        (
            _make_data_operation_node,
            FloatBasicProbe.input_data_type(),
            FloatBasicProbe.input_data_type(),
        ),
        (
            _make_probe_context_injector_node,
            FloatBasicProbe.input_data_type(),
            FloatBasicProbe.input_data_type(),
        ),
        (
            _make_probe_result_collector_node,
            FloatBasicProbe.input_data_type(),
            FloatBasicProbe.input_data_type(),
        ),
    ],
)
def test_data_type_delegation(factory, expected_in, expected_out):
    node = factory()
    assert node.input_data_type() is expected_in
    assert node.output_data_type() is expected_out


def test_processing_smoke_data_operation():
    node = _make_data_operation_node()
    payload = Payload(FloatBasicProbe.input_data_type()(3.0), ContextType())
    result = node.process(payload)
    assert isinstance(result.data, FloatBasicProbe.input_data_type())
    assert result.data.data == 6.0


def test_processing_smoke_probe_nodes():
    injector = _make_probe_context_injector_node()
    collector = _make_probe_result_collector_node()
    payload = Payload(FloatBasicProbe.input_data_type()(1.0), ContextType())
    result_inj = injector.process(payload)
    assert "probe_key" in result_inj.context.keys()
    result_col = collector.process(payload)
    assert result_col.context is payload.context
    assert collector.get_collected_data()


def test_processing_smoke_data_source_node():
    node = _make_data_source_node()
    no_payload = Payload(NoDataType(), ContextType())
    result = node.process(no_payload)
    assert isinstance(result.data, FloatBasicProbe.input_data_type())


def test_processing_smoke_payload_source_node():
    node = _make_payload_source_node()
    no_payload = Payload(NoDataType(), ContextType())
    result = node.process(no_payload)
    assert isinstance(result.data, FloatBasicProbe.input_data_type())


def test_processing_smoke_sink_nodes():
    data_sink = _make_data_sink_node()
    payload_sink = _make_payload_sink_node()
    payload = Payload(FloatBasicProbe.input_data_type()(5.0), ContextType())
    res_dsink = data_sink.process(payload)
    assert res_dsink.data.data == 5.0
    res_psink = payload_sink.process(payload)
    assert res_psink.data.data == 5.0


def test_type_mismatch_raises():
    node = _make_data_sink_node()

    class StringDataType(BaseDataType[str]):
        def validate(self, data: str) -> bool:
            return True

    bad_payload = Payload(StringDataType("oops"), ContextType())
    with pytest.raises(TypeError):
        node.process(bad_payload)


def test_logger_defaulting_and_preservation():
    node = _make_data_operation_node()
    assert isinstance(node.logger, Logger)
    custom = Logger(level="ERROR", console_output=False)
    node2 = _pipeline_node_factory(
        {"processor": FloatMultiplyOperation, "parameters": {"factor": 2.0}},
        custom,
    )
    assert node2.logger is custom


def test_context_key_injection_behavior():
    node = _make_probe_context_injector_node()
    ctx = ContextType()
    payload = Payload(FloatBasicProbe.input_data_type()(1.0), ctx)
    result = node.process(payload)
    assert result.context is ctx
    assert ctx.get_value("probe_key")
