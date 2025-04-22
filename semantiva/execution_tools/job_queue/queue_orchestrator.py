import uuid
import queue
import threading
from concurrent.futures import Future
from typing import Any, Dict, List, Optional, Union

from semantiva.execution_tools.transport.base import SemantivaTransport
from semantiva.payload_operations.pipeline import Pipeline
from semantiva.configurations.load_pipeline_from_yaml import load_pipeline_from_yaml
from semantiva.logger.logger import Logger
from .logging_setup import _setup_log

PipelineConfig = Union[Pipeline, List[Dict[str, Any]], str]


class QueueSemantivaOrchestrator:
    def __init__(
        self,
        transport: SemantivaTransport,
        stop_event: threading.Event | None = None,
        logger: Logger | None = None,
    ):
        self.transport = transport
        self.job_queue: queue.Queue = queue.Queue()
        self.pending_futures: Dict[str, Future] = {}
        self.logger = logger or _setup_log("master")
        self.running = False
        self.stop_event = stop_event

    def enqueue(
        self,
        pipeline_cfg: PipelineConfig,
        *,
        data: Any = None,
        context=None,
        return_future: bool = False,
    ) -> Optional[Future]:
        """
        Enqueue a new pipeline job.

        Args:
            pipeline_cfg: Pipeline instance, list of node dicts, or YAML str
            data: optional initial data payload
            context: optional initial context dict
            return_future: if True, returns a Future whose .result() is (data, context)
        """
        job_id: str = str(uuid.uuid4())
        job_payload = {"pipeline": pipeline_cfg, "data": data, "context": context or {}}
        fut: Future | None = Future() if return_future else None
        if return_future and fut:
            self.pending_futures[job_id] = fut
        self.job_queue.put((job_id, job_payload))
        self.logger.info(f"Enqueued job {job_id}")
        return fut

    def run_forever(self):
        self.logger.info("Master starting…")
        self.running = True
        self.transport.connect()

        while self.running:
            # 1) Dequeue and publish any new jobs
            try:
                job_id, payload = self.job_queue.get(timeout=0.2)
            except queue.Empty:
                payload = None

            if payload is not None:
                self.logger.info(f"Publishing jobs.{job_id}.cfg")
                self.transport.publish(
                    f"jobs.{job_id}.cfg",
                    data=payload,
                    context={"job_id": job_id},
                    metadata=None,
                    require_ack=False,
                )

            # 2) Subscribe to any status messages
            sub = self.transport.subscribe("jobs.*.status")
            for msg in sub:
                jid = msg.context.get_value("job_id")
                self.logger.info(f"Master received status for job {jid}")
                if jid in self.pending_futures:
                    # deliver full (data, context)
                    self.pending_futures[jid].set_result((msg.data, msg.context))
                    del self.pending_futures[jid]
                # ack if supported
                try:
                    msg.ack()
                except Exception:
                    pass
                break  # handle one message per cycle
            sub.close()
            if self.stop_event and self.stop_event.is_set():
                self.logger.info("Master stopping due to stop event.")
                break

    def stop(self):
        self.logger.info("Master stopping…")
        self.running = False
        self.transport.close()
