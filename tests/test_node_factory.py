import inspect
import pytest

from semantiva.payload_operations.nodes.node_factory import node_factory
from semantiva.tools.pipeline_inspector import PipelineInspector
from semantiva.examples.test_utils import (
    FloatDataSource,
    FloatPayloadSource,
    FloatDataSink,
    FloatPayloadSink,
    FloatMultiplyOperation,
    FloatCollectValueProbe,
)


def test_node_factory_creates_all_supported_nodes_and_semantic_ids():
    configs = [
        {"processor": FloatDataSource},
        {"processor": FloatPayloadSource},
        {"processor": FloatDataSink},
        {"processor": FloatPayloadSink},
        {"processor": FloatMultiplyOperation},
        {"processor": FloatCollectValueProbe, "context_keyword": "probe_key"},
        {"processor": FloatCollectValueProbe},
        {"processor": "rename:foo:bar"},
    ]

    nodes = [node_factory(cfg) for cfg in configs]
    report = PipelineInspector.get_nodes_semantic_ids_report(nodes)
    for node in nodes:
        assert node.semantic_id() in report


def test_datasource_node_propagates_docstring():
    node = node_factory({"processor": FloatDataSource})
    ds_doc = inspect.getdoc(FloatDataSource)
    generated_doc = inspect.getdoc(node.processor.__class__)
    assert ds_doc == generated_doc
