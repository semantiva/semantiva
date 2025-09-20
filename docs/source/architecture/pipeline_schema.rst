Pipeline Configuration Schema
=============================

Semantiva pipeline YAML supports declarative configuration of execution and tracing
behaviour alongside the node graph. The following optional top-level sections
extend the base ``pipeline.nodes`` definition:

``execution``
   Resolve orchestrators, executors, and transports from the registry. When
   omitted, the local sequential orchestrator with the in-memory transport is
   used.

   .. code-block:: yaml

      execution:
        orchestrator: LocalSemantivaOrchestrator
        executor: SequentialSemantivaExecutor
        transport: InMemorySemantivaTransport
        options:
          retries: 2

``trace``
   Configure tracing backends. The driver name is resolved via the registry,
   with ``jsonl`` and ``none`` supported out of the box. ``output_path`` accepts
   either a directory (a timestamped ``*.ser.jsonl`` file is created) or a
   concrete file path. Arbitrary driver keyword arguments can be supplied via
   ``options``.

   .. code-block:: yaml

      trace:
        driver: jsonl
        output_path: ./ser/run.ser.jsonl
        options:
          detail: all

``fanout``
   Declaratively expand a pipeline into multiple runs by injecting values into
   the execution context. Two modes are supported:

   ``param`` / ``values``
      Single-parameter fan-out. Each value is injected into the context under
      ``param`` for an independent run.

   ``multi``
      Multiple parameters zipped together. All lists must have equal length.

   Values can be embedded inline or loaded from ``values_file`` (JSON or YAML).
   The ``mode`` field is reserved for future expansion and currently defaults to
   ``zip``.

   .. code-block:: yaml

      fanout:
        multi:
          value: [3.0, 5.0, 9.5]
          factor: [2.0, 3.0, 5.0]

Each fan-out run produces SER evidence with ``why_ok.args`` populated with the
fan-out index, mode, injected values, and source metadata (including SHA-256
hashes when values originate from external files). This guarantees reproducible
audit trails for batch executions. See :doc:`../cli` for CLI flags mirroring the
schema and :doc:`../examples_index` for runnable examples.
