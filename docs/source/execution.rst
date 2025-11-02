Execution
=========

The execution module provides the orchestration infrastructure for running Semantiva pipelines.
It includes comprehensive error handling and integration with the tracing system to capture
complete execution records, including error events with timing data and exception details.

Component Registry System
--------------------------

Semantiva uses a dual-registry architecture to manage execution components while avoiding
circular import dependencies:

:py:class:`~semantiva.execution.component_registry.ExecutionComponentRegistry`
    Specialized registry for orchestrators, executors, and transports. This registry
    is designed to break circular import dependencies with the main ProcessorRegistry
    and graph builder modules.

:py:func:`~semantiva.execution.orchestrator.factory.build_orchestrator`
    Factory function that uses ExecutionComponentRegistry to construct orchestrators
    from configuration, supporting dependency injection of executors and transports.

The component registry follows the dependency inversion principle, acting as a dependency
sink rather than creating webs of interdependence. See :doc:`architecture/registry`
for detailed architectural information.

Template-method orchestrator
----------------------------

The core lifecycle now lives in
:py:class:`~semantiva.execution.orchestrator.orchestrator.SemantivaOrchestrator`.
It canonicalises the pipeline, snapshots context before/after each node, collects
``context_delta`` details, emits built-in pre/post assertions, and attaches environment
pins for every SER. Concrete orchestrators implement only two hooks:

``_submit_and_wait(node_callable, *, ser_hooks)``
    Runs a node and returns its :py:class:`~semantiva.pipeline.payload.Payload`.

``_publish(node, data, context, transport)``
    Forwards the node output through the orchestrator's transport.

All error handling, timing, and tracing responsibilities are handled by the
base class. ``LocalSemantivaOrchestrator`` simply delegates to the injected
executor/transport while benefiting from the shared SER logic.

During ``on_pipeline_start`` the orchestrator also emits a semantic fingerprint:
``pipeline_config_id`` summarises the set of ``(node_uuid, semantic_id)`` pairs
computed from live processor metadata, and ``node_semantic_ids`` exposes the
per-node values used in that hash. Structural identifiers (``pipeline_id`` and
node UUIDs) remain unchanged.

Public API Surface
------------------

- Component Registry: :py:mod:`semantiva.execution.component_registry`
- Orchestrator Factory: :py:mod:`semantiva.execution.orchestrator.factory`
- Executors: :py:mod:`semantiva.execution.executor.executor`
- Orchestrators: :py:mod:`semantiva.execution.orchestrator.orchestrator`
- Transports: :py:mod:`semantiva.execution.transport.in_memory`
- Job Queue: :py:mod:`semantiva.execution.job_queue.queue_orchestrator`

Autodoc
-------

.. automodule:: semantiva.execution.component_registry
   :members:
   :undoc-members:

.. automodule:: semantiva.execution.orchestrator.factory
   :members:
   :undoc-members:

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
