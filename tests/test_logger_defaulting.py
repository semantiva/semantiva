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

from typing import List

from semantiva.logger import Logger
from semantiva.examples.test_utils import FloatMultiplyOperation
from semantiva.pipeline.nodes._pipeline_node_factory import _pipeline_node_factory
from semantiva.context_processors.context_processors import ContextProcessor


class DummyContextProcessor(ContextProcessor):
    def _process_logic(self) -> None:
        # Dummy processor does nothing
        pass

    @classmethod
    def context_keys(cls) -> List[str]:
        return []


def test_data_operation_logger_default_and_custom():
    op_default = FloatMultiplyOperation()
    assert isinstance(op_default.logger, Logger)
    custom = Logger()
    op_custom = FloatMultiplyOperation(logger=custom)
    assert op_custom.logger is custom


def test_context_processor_logger_default_and_custom():
    cp_default = DummyContextProcessor()
    assert isinstance(cp_default.logger, Logger)
    custom = Logger()
    cp_custom = DummyContextProcessor(logger=custom)
    assert cp_custom.logger is custom


def test_factory_node_logger_propagation():
    config = {"processor": FloatMultiplyOperation}
    node_default = _pipeline_node_factory(config)
    assert isinstance(node_default.logger, Logger)
    assert isinstance(node_default.processor.logger, Logger)
    custom = Logger()
    node_custom = _pipeline_node_factory(config, logger=custom)
    assert node_custom.logger is custom
    assert node_custom.processor.logger is custom
