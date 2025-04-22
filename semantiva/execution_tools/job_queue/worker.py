import time
from threading import Event
from typing import Any, Dict, List, Union
from semantiva.execution_tools.transport.base import SemantivaTransport, Message
from semantiva.data_types import NoDataType
from semantiva.context_processors.context_processors import ContextType
from semantiva.execution_tools.executor.executor import SemantivaExecutor
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.configurations.load_pipeline_from_yaml import load_pipeline_from_yaml
from semantiva.logger.logger import Logger
from .logging_setup import _setup_log
import semantiva


def worker_loop(
    worker_id: int,
    transport: SemantivaTransport,
    executor: SemantivaExecutor,
    stop_event: Event,
    logger: Logger | None = None,
    poll_interval: float = 0.1,
):
    """
    Worker:
      - loops while not stop_event.is_set()
      - subscribes to 'jobs.*.cfg', processes messages, sleeps if none
      - exits when stop_event is set
    """
    worker_logger: semantiva.logger.logger.Logger = logger or _setup_log(
        f"worker_{worker_id}"
    )
    assert logger, "Logger must be provided or created"
    worker_logger.info(f"Worker_{worker_id} starting…")
    transport.connect()

    try:
        while not stop_event.is_set():
            sub = transport.subscribe("jobs.*.cfg")
            got_message = False

            for msg in sub:
                got_message = True
                job_id = msg.context.get("job_id", "<unknown>")
                worker_logger.info(f"Picked up job {job_id}")

                payload = msg.data
                logger.debug(f"Worker {job_id} received message: {msg}")
                try:
                    # Unpack: pipeline config, data, context
                    pcfg = payload["pipeline"]["pipeline"]
                    data = payload.get("data", NoDataType())
                    context = payload.get("context", ContextType())

                    logger.debug(
                        f"Worker {job_id} received job with data: {data}, context: {context}, pcfg: {pcfg}"
                    )

                    # Instantiate pipeline
                    if isinstance(pcfg, Pipeline):
                        pipeline = pcfg
                    elif isinstance(pcfg, list):
                        pipeline = Pipeline(pcfg, logger=worker_logger)
                    elif isinstance(pcfg, str):
                        nodes = load_pipeline_from_yaml(pcfg)
                        pipeline = Pipeline(nodes)
                    else:
                        raise TypeError(f"Unsupported pipeline config: {type(pcfg)}")

                    # Execute
                    result_data, result_ctx = pipeline.process(
                        data=data, context=context
                    )
                    result_ctx.set_value(
                        "job_id", job_id
                    )  # Set job_id in context for tracking
                    # Publish result
                    transport.publish(
                        f"jobs.{job_id}.status",
                        data=result_data,
                        context=result_ctx,
                        require_ack=False,
                    )
                    worker_logger.info(f"Completed job {job_id}")
                    msg.ack()
                except Exception as e:
                    worker_logger.exception(f"Worker failed job {job_id}: {e}")

                # Let other work in same subscription pass through before closing
            sub.close()

            if not got_message:
                time.sleep(poll_interval)
    except Exception as e:
        worker_logger.exception(f"Worker loop exception: {e}")
    finally:
        transport.close()
        worker_logger.info("Worker shutting down.")
