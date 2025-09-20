Execution
=========

The execution module provides the orchestration infrastructure for running Semantiva pipelines.
It includes comprehensive error handling and integration with the tracing system to capture
complete execution records, including error events with timing data and exception details.

Template-method orchestrator
----------------------------

The core lifecycle now lives in
:py:class:`~semantiva.execution.orchestrator.orchestrator.SemantivaOrchestrator`.
It canonicalises the pipeline, snapshots context before/after each node, collects
``io_delta`` details, emits built-in pre/post checks, and attaches environment
pins for every SER. Concrete orchestrators implement only two hooks:

``_submit_and_wait(node_callable, *, ser_hooks)``
    Runs a node and returns its :py:class:`~semantiva.pipeline.payload.Payload`.

``_publish(node, data, context, transport)``
    Forwards the node output through the orchestrator's transport.

All error handling, timing, and tracing responsibilities are handled by the
base class. ``LocalSemantivaOrchestrator`` simply delegates to the injected
executor/transport while benefiting from the shared SER logic.

Public API Surface
------------------

- Executors: :py:mod:`semantiva.execution.executor.executor`
- Orchestrators: :py:mod:`semantiva.execution.orchestrator.orchestrator`
- Transports: :py:mod:`semantiva.execution.transport.in_memory`
- Job Queue: :py:mod:`semantiva.execution.job_queue.queue_orchestrator`

Autodoc
-------

.. automodule:: semantiva.execution.executor.executor
   :members:
   :undoc-members:

.. automodule:: semantiva.execution.orchestrator.orchestrator
   :members:
   :undoc-members:

.. automodule:: semantiva.execution.transport.base
   :members:
   :undoc-members:

.. automodule:: semantiva.execution.transport.in_memory
   :members:
   :undoc-members:

.. automodule:: semantiva.execution.job_queue.queue_orchestrator
   :members:
   :undoc-members:
