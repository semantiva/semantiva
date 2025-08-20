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

import threading
import os

from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.execution.executor.executor import SequentialSemantivaExecutor
from semantiva.execution.job_queue.queue_orchestrator import (
    QueueSemantivaOrchestrator,
)
from semantiva.execution.job_queue.logging_setup import _setup_log
from semantiva.execution.job_queue.worker import worker_loop
from semantiva.examples.test_utils import FloatDataType
import math


def test_job_execution_with_yaml_pipeline(tmp_path):
    # Use the provided pipeline YAML in tests directory
    tests_dir = os.path.dirname(__file__)
    yaml_path = os.path.join(tests_dir, "pipeline_config.yaml")
    assert os.path.exists(yaml_path), "Expected pipeline_config.yaml in tests/"

    # 1) Set up transport and master orchestrator
    transport = InMemorySemantivaTransport()
    master_logger = _setup_log("test_master_yaml", level="DEBUG")
    orchestrator = QueueSemantivaOrchestrator(
        transport=transport,
        stop_event=None,  # we'll stop manually later
        logger=master_logger,
    )

    # 2) Start the master loop in a daemon thread
    master_thread = threading.Thread(target=orchestrator.run_forever, daemon=True)
    master_thread.start()

    # 3) Prepare a worker
    stop_event = threading.Event()
    worker_logger = _setup_log("test_worker_yaml", level="DEBUG")
    worker_executor = SequentialSemantivaExecutor()
    t = threading.Thread(
        target=worker_loop,
        args=(0, transport, worker_executor, stop_event, worker_logger),
        daemon=True,
    )
    t.start()

    # 4) Enqueue a job where pipeline metadata is a path to the YAML file
    # The YAML pipeline begins with a DataSource, so do not provide input data
    future = orchestrator.enqueue(yaml_path, return_future=True)

    # 5) Wait for the Future and assert results
    result, context = future.result(timeout=10)

    # Expect the pipeline to produce a FloatDataType result (starts with DataSource)
    assert isinstance(
        result, FloatDataType
    ), f"Expected FloatDataType, got {type(result)}"

    # Ensure job id was propagated into the resulting context
    assert context.get_value("job_id") is not None

    # Validate the numeric pipeline progression matches the YAML-defined steps
    step1 = 42.0
    step2 = step1 * 2.5
    step3 = step2**2
    step4 = step3 + step1
    step5 = math.sqrt(step4)
    expected_final_value = step5 / 3.0
    assert (
        abs(result.data - expected_final_value) < 0.001
    ), f"Expected {expected_final_value}, got {result.data}"

    # Confirm final probe is present and matches the computed value
    final_probe = context.get_value("final_value")
    assert isinstance(final_probe, dict)
    assert (
        abs(final_probe.get("value", 0.0) - expected_final_value) < 0.001
    ), f"Expected context final_value {expected_final_value}, got {final_probe.get('value')}"
