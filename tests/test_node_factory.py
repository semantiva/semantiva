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

import inspect

from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
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

    nodes = [_pipeline_node_factory(cfg) for cfg in configs]
    for node in nodes:
        assert isinstance(node.semantic_id(), str)


def test_datasource_node_propagates_docstring():
    node = _pipeline_node_factory({"processor": FloatDataSource})
    ds_doc = inspect.getdoc(FloatDataSource)
    generated_doc = inspect.getdoc(node.processor.__class__)
    assert ds_doc == generated_doc
