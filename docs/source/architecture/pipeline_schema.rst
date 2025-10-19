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

``run_space``
   Define a set of runs by expanding context keys. A run space contains:

   ``combine``
      How blocks combine globally. ``combinatorial`` (default) computes a Cartesian
      product across blocks; ``by_position`` requires blocks to have identical run
      counts and aligns them by index.

   ``max_runs``
      Safety limit on the total number of runs. The planner raises a
      configuration error when the expansion exceeds this cap.

   ``dry_run``
      When ``true``, the planner reports the expansion (sizes, block metadata,
      sample runs) and exits before executing nodes.

   ``blocks``
      A list of block objects. Each block defines ``mode`` (``by_position`` or
      ``combinatorial``) and either ``context`` (mapping of key -> list) or
      ``source`` (CSV/JSON/YAML/NDJSON file with optional ``select``/``rename``).
      Sources follow rows-as-runs semantics: each row/object becomes one run,
      and the block's ``mode`` controls whether lists are aligned by index or
      combined combinatorially. ``by_position`` blocks require all lists to have
      equal length; ``combinatorial`` blocks compute full Cartesian products within
      the block. Duplicate context keys across blocks (or within a block between
      ``context`` and ``source``) raise an error.

   .. code-block:: yaml

      run_space:
        blocks:
          - mode: by_position
            context:
              value: [3.0, 5.0, 9.5]
              factor: [2.0, 3.0, 5.0]
          - mode: combinatorial
            context:
              seed: [1, 2]
              batch_size: [16, 32]

Validation
----------

The loader enforces strict shapes for these blocks:

- ``execution.options`` must be a mapping
- ``trace.options`` must be a mapping
- Singular ``option`` keys are invalid in both blocks and will produce a clear error

Refer to :doc:`../cli` for the corresponding command-line flags and to
:doc:`../examples_index` for runnable YAML examples.

Each run-space expansion produces SER evidence with ``assertions.args`` populated
with ``run_space.index``, ``run_space.total``, ``run_space.combine``, and the
per-run context. Block metadata includes source provenance (path, type,
SHA-256) when external files are involved. See :doc:`../cli` for CLI flags
mirroring the schema and :doc:`../examples_index` for runnable examples.
