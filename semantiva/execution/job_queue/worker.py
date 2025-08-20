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
Defines the `worker_loop` function, which continuously listens for new pipeline jobs
via a SemantivaTransport, executes them using a SemantivaExecutor, and publishes results.
"""

import time
from threading import Event
from typing import Optional

from semantiva.execution.transport.base import SemantivaTransport
from semantiva.data_types import NoDataType
from semantiva.context_processors.context_processors import ContextType
from semantiva.execution.executor.executor import SemantivaExecutor
from semantiva import Pipeline, Payload
from semantiva.logger.logger import Logger
from .logging_setup import _setup_log
from semantiva.configurations.load_pipeline_from_yaml import load_pipeline_from_yaml


def worker_loop(
    worker_id: int,
    transport: SemantivaTransport,
    executor: SemantivaExecutor,
    stop_event: Event,
    logger: Optional[Logger] = None,
    poll_interval: float = 0.1,
):
    """
    Main worker loop for processing Semantiva pipeline jobs.

    Args:
        worker_id: Unique identifier for this worker instance.
        transport: A SemantivaTransport implementation for pub/sub.
        executor: A SemantivaExecutor to run pipeline tasks.
        stop_event: Threading Event used to signal shutdown.
        logger: Optional Logger instance; if None, one is created via _setup_log.
        poll_interval: Seconds to sleep when no job is found.

    Behavior:
      1. Connects to the transport.
      2. Repeatedly:
         a. Subscribes to 'jobs.*.cfg' to receive new job payloads.
         b. For each Message:
            - Extract job_id, pipeline config, initial data, and context.
            - Instantiate a Pipeline object (from dict, YAML, or direct instance).
            - Call pipeline.process(data, context) to execute.
            - Publish the result to 'jobs.<job_id>.status'.
            - Acknowledge the incoming message if supported.
         c. Closes the subscription.
         d. If no messages were processed, sleeps for `poll_interval`.
      3. Exits when stop_event.is_set(), closes transport, logs shutdown.

    This allows multiple workers to run in parallel, distributing jobs across processes
    or containers while decoupling job submission (by the orchestrator) from execution.
    """
    # Initialize or reuse the logger for this worker
    worker_logger: Logger = logger or _setup_log(f"worker_{worker_id}")
    assert worker_logger, "Logger must be provided or created"
    worker_logger.info(f"Worker_{worker_id} starting…")

    # Establish transport connection (no-op for in-memory, real for NATS/Kafka, etc.)
    transport.connect()

    try:
        # Continue looping until an external shutdown signal is received
        while not stop_event.is_set():
            # Subscribe to job configuration messages (pattern supports wildcards)
            sub = transport.subscribe("jobs.*.cfg")
            got_message = False

            # Process each incoming job message
            for msg in sub:
                got_message = True
                job_id = msg.metadata.get("job_id") or "<unknown>"
                worker_logger.info(f"Picked up job {job_id}")

                # Optional debug output of the raw Message
                worker_logger.debug(f"Worker {job_id} received message: {msg}")

                try:
                    # 1) Unpack the payload dictionary
                    pcfg = msg.metadata.get("pipeline")
                    # If pipeline metadata is a path to a YAML file, load it
                    if isinstance(pcfg, str):
                        try:
                            pcfg = load_pipeline_from_yaml(pcfg)
                        except Exception as e:
                            worker_logger.error(
                                f"Failed to load pipeline YAML for job {job_id} from '{pcfg}': {e}"
                            )
                            try:
                                msg.ack()
                            except Exception:
                                pass
                            continue
                    if not isinstance(pcfg, list) or not all(
                        isinstance(step, dict) for step in pcfg
                    ):
                        worker_logger.error(
                            f"Invalid pipeline configuration received for job {job_id}: {pcfg}"
                        )
                        msg.ack()  # acknowledge to remove the message if applicable
                        continue  # skip processing this message
                    data = msg.data or NoDataType()
                    context = msg.context or ContextType()

                    worker_logger.debug(
                        f"Worker {job_id} has data={data}, context={context}, pcfg={pcfg}"
                    )

                    # 2) Instantiate the Pipeline object
                    if isinstance(pcfg, list):
                        pipeline = Pipeline(pcfg, logger=worker_logger)
                    else:
                        raise TypeError(f"Unsupported pipeline config: {type(pcfg)}")

                    # 3) Execute the pipeline with provided executor

                    pipeline_output = executor.submit(
                        pipeline.process, Payload(data, context)
                    )
                    result_payload = pipeline_output.result()
                    result_data, result_ctx = (
                        result_payload.data,
                        result_payload.context,
                    )

                    # 4) Annotate context with job_id for master correlation
                    result_ctx.set_value("job_id", job_id)

                    # 5) Publish the result to status channel
                    transport.publish(
                        f"jobs.{job_id}.status",
                        data=result_data,
                        context=result_ctx,
                        require_ack=False,
                    )
                    worker_logger.info(f"Completed job {job_id}")

                    # 6) Acknowledge the incoming message if transport supports it
                    msg.ack()
                except Exception as e:
                    # Log any error during processing without crashing the loop
                    worker_logger.exception(f"Worker failed job {job_id}: {e}")

            # Close this subscription before the next polling iteration
            sub.close()

            # If no messages arrived, sleep briefly to avoid busy-looping
            if not got_message:
                time.sleep(poll_interval)

    except Exception as e:
        # Catch-all: ensure unexpected exceptions are logged
        worker_logger.exception(f"Worker loop exception: {e}")
    finally:
        # Clean up transport connection and log shutdown
        transport.close()
        worker_logger.info("Worker shutting down.")
