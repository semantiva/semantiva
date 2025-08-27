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
job_demo.py

Example script demonstrating usage of QueueSemantivaOrchestrator with InMemorySemantivaTransport
and worker_loop to run multiple pipeline jobs in parallel on a single host.

This mirrors the test_job_execution() setup:
  - Starts the master orchestrator in a background thread
  - Spins up two worker threads, each running worker_loop(...)
  - Enqueues two jobs with simple pipeline configurations
  - Waits on Future.result() for each job’s output
  - Shuts down master and workers cleanly via a shared stop_event
"""

import threading
import time

from semantiva.execution.transport.in_memory import InMemorySemantivaTransport
from semantiva.execution.executor.executor import SequentialSemantivaExecutor
from semantiva.execution.job_queue.queue_orchestrator import (
    QueueSemantivaOrchestrator,
)
from semantiva.execution.job_queue.worker import worker_loop
from semantiva.execution.job_queue.logging_setup import _setup_log
from semantiva.examples.test_utils import (
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatValueDataSource,
)

# If you want to demonstrate a non-trivial pipeline, import or define node configurations here:
# from semantiva.payload_operations.pipeline import Pipeline
# example_nodes = [ ... ]
LOG_LEVEL = "DEBUG"  # Set to "INFO" for less verbosity


def main():
    """Run a demonstration of the queue-based orchestrator with worker threads."""
    # 1) Prepare transport, executor, orchestrator, and logging
    transport = InMemorySemantivaTransport()
    executor = SequentialSemantivaExecutor()
    master_logger = _setup_log("demo_master", level=LOG_LEVEL)
    orchestrator = QueueSemantivaOrchestrator(
        transport=transport,
        stop_event=None,  # we'll call orchestrator.stop() manually
        logger=master_logger,
    )

    # 2) Start the master orchestrator in its own daemon thread
    master_thread = threading.Thread(target=orchestrator.run_forever, daemon=True)
    master_thread.start()

    # 3) Shared event to signal workers to exit
    stop_event = threading.Event()

    # 4) Launch two worker threads, each with its own logger
    worker_threads = []
    for worker_id in range(2):
        worker_logger = _setup_log(f"demo_worker_{worker_id}", level=LOG_LEVEL)
        t = threading.Thread(
            target=worker_loop,
            args=(worker_id, transport, executor, stop_event, worker_logger),
            daemon=True,
        )
        t.start()
        worker_threads.append(t)

    # 5) Define a simple pipeline configuration

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

    example_job_cfg = node_configurations

    # 6) Enqueue two jobs, requesting Future results
    future1 = orchestrator.enqueue(
        example_job_cfg,
        return_future=True,
        data=FloatValueDataSource.get_data(),
        context=None,
    )
    future2 = orchestrator.enqueue(
        example_job_cfg,
        return_future=True,
        data=FloatValueDataSource.get_data(),
        context=None,
    )

    # 7) Wait for each job to complete and print the results
    print("Waiting for job 1 result...")
    result1, context1 = future1.result(timeout=10)
    print(f"Job 1 completed with result: {result1.data}, context: {context1}")

    print("Waiting for job 2 result...")
    result2, context2 = future2.result(timeout=10)
    print(f"Job 2 completed with result: {result2.data}, context: {context2}")

    # 8) Graceful shutdown
    print("Shutting down orchestrator...")
    orchestrator.stop()

    print("Signaling workers to stop...")
    stop_event.set()

    # Give threads a moment to exit
    time.sleep(0.2)
    print("Demo complete.")


if __name__ == "__main__":
    main()
