Pipeline Configuration Schema
=============================

Semantiva pipeline YAML supports declarative configuration of execution and tracing
behaviour alongside the node graph. The following optional top-level sections
extend the base ``pipeline.nodes`` definition:

``execution``
   Resolve orchestrators, executors, and transports from the registry. When
   omitted, the local sequential orchestrator with the in-memory transport is
   used.

   Only the plural key ``options`` is accepted for additional execution options.
   Using ``option`` is invalid and will raise a configuration error.

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
   concrete file path. Arbitrary driver keyword arguments must be supplied via
   the plural key ``options``.

   Detail flags (for the JSONL driver) control how much evidence is captured:

   - ``hash`` (default): include SHA-256 digests for input/output data and context
   - ``repr``: additionally include ``repr`` for input/output data
   - ``context``: with ``repr``, also include ``repr`` for pre/post context
   - ``all``: enable ``hash`` + ``repr`` + ``context``

   .. note::
      Only ``options`` is valid in this block. ``option`` is not accepted.

   .. code-block:: yaml

      trace:
        driver: jsonl
        output_path: ./ser/
        options:
          detail: all

    The CLI mirrors these keys; for example:

    .. code-block:: bash

         semantiva run my_pipeline.yaml \
            --trace.driver jsonl \
            --trace.output ./ser/ \
            --trace.option detail=all

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

Validation
----------

The loader enforces strict shapes for these blocks:

- ``execution.options`` must be a mapping
- ``trace.options`` must be a mapping
- Singular ``option`` keys are invalid in both blocks and will produce a clear error

Refer to :doc:`../cli` for the corresponding command-line flags and to
:doc:`../examples_index` for runnable YAML examples.

Each fan-out run produces SER evidence with ``why_ok.args`` populated with the
fan-out index, mode, injected values, and source metadata (including SHA-256
hashes when values originate from external files). This guarantees reproducible
audit trails for batch executions. See :doc:`../cli` for CLI flags mirroring the
schema and :doc:`../examples_index` for runnable examples.
