import pytest

from semantiva.execution_tools.transport.in_memory import InMemorySemantivaTransport
from semantiva.execution_tools.executor.executor import SequentialSemantivaExecutor
from semantiva.execution_tools.job_queue.queue_orchestrator import (
    QueueSemantivaOrchestrator,
)
from semantiva.execution_tools.job_queue.logging_setup import _setup_log
from semantiva.execution_tools.job_queue.worker import worker_loop
import threading
import time
from .test_utils import (
    FloatMultiplyOperation,
    FloatCollectValueProbe,
    FloatMockDataSource,
)


def test_job_execution():
    """Test the execution of a pipeline with multiple nodes."""

    transport = InMemorySemantivaTransport()

    orchestrator = QueueSemantivaOrchestrator(
        transport=transport, logger=_setup_log("master", level="DEBUG")
    )

    master_thread = threading.Thread(target=orchestrator.run_forever, daemon=True)
    master_thread.start()

    stop_event = threading.Event()
    worker_threads = []
    for worker_id in range(2):
        worker_logger = _setup_log(f"worker_{worker_id}", level="DEBUG")
        worker_executor = SequentialSemantivaExecutor()
        t = threading.Thread(
            target=worker_loop,
            args=(worker_id, transport, worker_executor, stop_event, worker_logger),
            daemon=True,
        )
        t.start()
        worker_threads.append(t)
    # Enqueue example jobs

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

    example_job_cfg = {"pipeline": node_configurations}  # Simplified example config

    future1 = orchestrator.enqueue(
        example_job_cfg, return_future=True, data=FloatMockDataSource().get_data()
    )
    future2 = orchestrator.enqueue(
        example_job_cfg, return_future=True, data=FloatMockDataSource().get_data()
    )

    # Wait for results
    print("Waiting for job 1 result...")
    result1, context1 = future1.result(timeout=10)
    print(f"Job 1 completed with result: {result1}, context: {context1}")

    print("Waiting for job 2 result...")
    result2, context2 = future2.result(timeout=10)
    print(f"Job 2 completed with result: {result2}, context: {context2}")

    # Graceful shutdown
    print("Shutting down orchestrator...")
    orchestrator.stop()
    print("Shutting down workers...")
    stop_event.set()
    time.sleep(0.1)


if __name__ == "__main__":
    test_job_execution()
