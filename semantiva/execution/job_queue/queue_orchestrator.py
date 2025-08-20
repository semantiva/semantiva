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
Defines QueueSemantivaOrchestrator, the "master" component in Semantiva's distributed
job-execution framework. This orchestrator:

  - Accepts pipeline jobs (config + optional data/context) via enqueue().
  - Maintains a FIFO in-memory queue of pending jobs.
  - Fans out each job by publishing a `jobs.<id>.cfg` message over a SemantivaTransport.
  - Listens for `jobs.<id>.status` messages to resolve per-job Future objects.
  - Supports clean shutdown via a threading.Event signal or the stop() method.

This design decouples job submission, transport, and result collection, allowing
plugging in different transport and executor implementations without changing core logic.
"""

import uuid
import queue
import threading
from concurrent.futures import Future
from typing import Any, Dict, List, Optional, Union

from semantiva.execution.transport.base import SemantivaTransport
from semantiva.pipeline import Pipeline

from semantiva.data_types import BaseDataType
from semantiva.context_processors import ContextType
from semantiva.logger.logger import Logger
from .logging_setup import _setup_log


PipelineConfig = Union[Pipeline, List[Dict[str, Any]], str]


class QueueSemantivaOrchestrator:
    """
    Master orchestrator that enqueues and broadcasts independent Semantiva pipeline jobs.

    Attributes:
        transport:        Pluggable SemantivaTransport for pub/sub of jobs and statuses.
        job_queue:        In-memory FIFO queue of (job_id, payload) tuples.
        pending_futures:  Maps job_id → Future for callers awaiting results.
        logger:           Role-specific Logger for master metadata and timing.
        running:          Flag controlling the main publish-listen loop.
        stop_event:       Optional threading.Event that triggers graceful shutdown.
    """

    def __init__(
        self,
        transport: SemantivaTransport,
        stop_event: Optional[threading.Event] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            transport:  A SemantivaTransport implementation to publish and subscribe messages.
            stop_event: Optional Event; when set, the run_forever loop will exit.
            logger:     Optional Logger; if not provided, one is created via _setup_log.
        """
        # Core components
        self.transport = transport
        self.job_queue: queue.Queue = queue.Queue()
        self.pending_futures: Dict[str, Future] = {}

        # Logging and control flags
        self.logger = logger or _setup_log("master")
        self.running = False
        self.stop_event = stop_event
        self.logger.debug(
            f"Master initialized with transport={transport}, stop_event={stop_event}"
        )

    def enqueue(
        self,
        pipeline_cfg: PipelineConfig,
        *,
        data: Optional[BaseDataType] = None,
        context: Optional[ContextType] = None,
        return_future: bool = False,
    ) -> Optional[Future]:
        """
        Enqueue a new pipeline job for asynchronous execution.

        Args:
            pipeline_cfg:   A `Pipeline` instance, a list of node configuration
                dictionaries, or a path to a YAML configuration file.
            data:           Optional initial data.
            context:        Optional initial context.
            return_future:  If True, returns a Future whose result() yields
                ``(data, context)``.

        Returns:
            Future if return_future=True; otherwise None.
        """
        # 1) Generate a unique job identifier
        job_id: str = str(uuid.uuid4())

        # 2) Optionally create a Future to track this job’s completion
        fut: Optional[Future] = Future() if return_future else None
        if fut:
            self.pending_futures[job_id] = fut

        # 3) Place the job on the internal FIFO queue
        self.job_queue.put(
            (job_id, pipeline_cfg, data, context or ContextType())
        )  # Enqueue a tuple with (job_id, pipeline_cfg, data, context)
        self.logger.info(f"Enqueued job {job_id}")

        return fut

    def run_forever(self) -> None:
        """
        Main event loop:

        1) Dequeue and publish any newly enqueued jobs.
        2) Subscribe to 'jobs.*.status' channel and resolve matching Futures.
        3) Repeat until stop_event is set or stop() is called.
        """
        self.logger.info("Master starting…")
        self.running = True
        self.transport.connect()

        while self.running:
            # -- Publish phase --
            try:
                job_id, pipeline_cfg, data, context = self.job_queue.get(timeout=0.2)
            except queue.Empty:
                job_id = None

            if job_id is not None:
                self.logger.info(f"Publishing jobs.{job_id}.cfg")
                self.transport.publish(
                    f"jobs.{job_id}.cfg",
                    data=data,
                    context=context,
                    metadata={"job_id": job_id, "pipeline": pipeline_cfg},
                    require_ack=False,
                )

            # -- Listen for completions --
            sub = self.transport.subscribe("jobs.*.status")
            for msg in sub:
                self.logger.debug(f"Master received message: {msg}")
                # Extract the job ID from the returned context
                jid = msg.context.get_value("job_id")
                self.logger.info(f"Master received status for job {jid}")

                # If the user requested a Future, resolve it now
                if jid in self.pending_futures:
                    self.pending_futures[jid].set_result((msg.data, msg.context))
                    del self.pending_futures[jid]

                # Acknowledge receipt if transport supports it
                try:
                    msg.ack()
                except Exception:
                    pass

                # Only handle one message per iteration
                break
            sub.close()

            # -- Shutdown check --
            if self.stop_event and self.stop_event.is_set():
                self.logger.info("Master stopping due to stop event.")
                break

    def stop(self) -> None:
        """
        Signal the orchestrator to exit its run loop and close the transport.
        """
        self.logger.info("Master stopping…")
        self.running = False
        self.transport.close()
