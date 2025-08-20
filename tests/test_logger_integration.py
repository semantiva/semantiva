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

# Logger integration and propagation tests
# Ensures centralized logger initialization works across components and node factories.

import pickle
from semantiva.logger import Logger
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.context_processors.context_types import ContextType
from semantiva.pipeline import Payload
from semantiva.examples.test_utils import (
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    FloatMultiplyOperation,
    FloatBasicProbe,
)


def test_logger_pickling_roundtrip():
    log = Logger(level="DEBUG", console_output=False, name="PickleTest")
    dumped = pickle.dumps(log)
    restored = pickle.loads(dumped)
    assert isinstance(restored, Logger)
    # Same underlying logger name
    assert restored.logger.name == log.logger.name
    # Level should be at least as set (some environments may inherit root adjustments)
    assert restored.logger.level == log.logger.level


def _make_nodes(logger=None):
    return [
        _pipeline_node_factory({"processor": FloatDataSource}, logger),
        _pipeline_node_factory({"processor": FloatPayloadSource}, logger),
        _pipeline_node_factory({"processor": FloatDataSink}, logger),
        _pipeline_node_factory({"processor": FloatPayloadSink}, logger),
        _pipeline_node_factory({"processor": FloatMultiplyOperation}, logger),
        _pipeline_node_factory(
            {"processor": FloatBasicProbe, "context_keyword": "probe_ctx"}, logger
        ),
        _pipeline_node_factory({"processor": FloatBasicProbe}, logger),
    ]


def test_node_logger_defaulting_and_propagation():
    # Without explicit logger
    nodes = _make_nodes()
    for n in nodes:
        assert isinstance(n.logger, Logger)
        # Processor should share the same logger instance
        assert getattr(n.processor, "logger", None) is n.logger

    # With explicit logger
    custom = Logger(level="INFO", console_output=False, name="CustomNode")
    nodes_with = _make_nodes(custom)
    for n in nodes_with:
        assert n.logger is custom
        assert getattr(n.processor, "logger", None) is custom


def test_payload_source_context_injection_logger_stability():
    # Ensure executing a payload source node does not replace logger references
    custom = Logger(level="INFO", console_output=False, name="PayloadSrcTest")
    node = _pipeline_node_factory({"processor": FloatPayloadSource}, custom)
    original_logger = node.logger
    # Process a dummy initial payload (NoDataType semantics = data ignored); pass None for data
    payload = Payload(data=None, context=ContextType({}))  # type: ignore[arg-type]
    out = node.process(payload)
    assert out.context is not None
    assert node.logger is original_logger
    assert node.processor.logger is original_logger


def test_data_operation_node_logger_stability():
    custom = Logger(level="DEBUG", console_output=False, name="OpNode")
    node = _pipeline_node_factory({"processor": FloatMultiplyOperation}, custom)
    # Construct a valid FloatDataType input (e.g., value 2.0)
    input_instance = FloatMultiplyOperation.input_data_type()(2.0)  # type: ignore[call-arg]
    payload = Payload(input_instance, ContextType({}))
    # Provide required parameter if any through context or config; FloatMultiplyOperation in test_utils typically needs parameter 'factor'
    try:
        node.process(payload)
    except KeyError:
        # If 'factor' or others required, inject default value 1.0 into context and retry
        for pname in node.processor.get_processing_parameter_names():
            payload.context.set_value(pname, 1.0)
        node.process(payload)
    assert node.logger is custom
    assert node.processor.logger is custom
