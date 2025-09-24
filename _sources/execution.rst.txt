Execution
=========

The execution module provides the orchestration infrastructure for running Semantiva pipelines.
It includes comprehensive error handling and integration with the tracing system to capture
complete execution records, including error events with timing data and exception details.

The ``LocalSemantivaOrchestrator`` ensures that trace resources are properly managed even
when pipeline execution fails, providing robust error tracing capabilities for debugging
and monitoring pipeline behavior.

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
