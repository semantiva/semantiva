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
End-to-end integration test for Semantiva's Queue-Enabled Orchestrator and Worker.

This test validates the full cycle of:
  1. Enqueueing multiple pipeline jobs via QueueSemantivaOrchestrator.
  2. Distributing work to `worker_loop` instances running in parallel threads.
  3. Processing each pipeline step (FloatMultiply, FloatCollectValueProbe, renaming, deletion).
  4. Publishing results back to the orchestrator over InMemorySemantivaTransport.
  5. Resolving Future objects so callers can retrieve final (data, context).
  6. Graceful shutdown of master and workers via threading.Event.

Semantiva's transport layer (InMemorySemantivaTransport) and executor (SequentialSemantivaExecutor)
are used here for simplicity; in production you'd swap in NATS, Ray, etc.
"""

import threading
import time

from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.execution.executor.executor import SequentialSemantivaExecutor
from semantiva.execution.job_queue.queue_orchestrator import (
    QueueSemantivaOrchestrator,
)
from semantiva.execution.job_queue.logging_setup import _setup_log
from semantiva.execution.job_queue.worker import worker_loop
from semantiva.examples.test_utils import (
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatMockDataSource,
)


def test_job_execution():
    """
    Tests the execution of a multi-node pipeline through the master/worker queue:
      - Creates an in-memory transport and sequential executor.
      - Starts the QueueSemantivaOrchestrator in a background thread.
      - Launches two worker threads running worker_loop(...).
      - Enqueues two identical jobs, each multiplying and probing float data.
      - Blocks on Future.result() for each job to ensure correct outputs.
      - Shuts down the orchestrator and signals workers to exit cleanly.
    """

    # 1) Set up transport and master orchestrator
    transport = InMemorySemantivaTransport()
    master_logger = _setup_log("test_master", level="DEBUG")
    orchestrator = QueueSemantivaOrchestrator(
        transport=transport,
        stop_event=None,  # we'll stop manually later
        logger=master_logger,
    )

    # 2) Start the master loop in a daemon thread
    master_thread = threading.Thread(target=orchestrator.run_forever, daemon=True)
    master_thread.start()

    # 3) Prepare workers with a shared stop_event for graceful shutdown
    stop_event = threading.Event()
    worker_threads = []
    for worker_id in range(2):
        worker_logger = _setup_log(f"test_worker_{worker_id}", level="DEBUG")
        worker_executor = SequentialSemantivaExecutor()
        t = threading.Thread(
            target=worker_loop,
            args=(worker_id, transport, worker_executor, stop_event, worker_logger),
            daemon=True,
        )
        t.start()
        worker_threads.append(t)

    # 4) Define a multi-node pipeline configuration as a list of processor specs
    node_configurations = [
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 2},
        },
        {
            "processor": FloatMultiplyOperation,
            "parameters": {"factor": 3},
        },
        {
            "processor": FloatCollectValueProbe,
        },
        {
            "processor": FloatCollectValueProbe,
            "context_keyword": "mock_keyword",
        },
        {
            "processor": FloatCollectValueProbe,
            "context_keyword": "dummy_keyword",
        },
        {
            "processor": "rename:mock_keyword:final_keyword",
        },
        {
            "processor": "delete:dummy_keyword",
        },
    ]

    # 5) Enqueue two jobs with initial data from FloatMockDataSource
    input_data = FloatMockDataSource().get_data()
    future1 = orchestrator.enqueue(
        node_configurations, return_future=True, data=input_data
    )
    future2 = orchestrator.enqueue(
        node_configurations, return_future=True, data=input_data
    )

    # 6) Wait for each job's Future to complete and verify outputs
    print("Waiting for job 1 result...")
    result1, context1 = future1.result(timeout=10)
    print(f"Job 1 completed with result: {result1}, context: {context1}")

    print("Waiting for job 2 result...")
    result2, context2 = future2.result(timeout=10)
    print(f"Job 2 completed with result: {result2}, context: {context2}")

    # 7) Clean up: stop orchestrator and signal workers to exit
    print("Shutting down orchestrator...")
    orchestrator.stop()

    print("Shutting down workers...")
    stop_event.set()

    # Allow threads to finish
    time.sleep(0.1)


if __name__ == "__main__":
    # Allow standalone execution of this integration test
    test_job_execution()
