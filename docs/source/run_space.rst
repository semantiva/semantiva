Run Space (v1): blocks that expand context
==========================================

Semantiva's run space defines a set of executions by expanding **context** keys.
Each *block* expands its own keys using either ``by_position`` (index-aligned)
or ``combinatorial`` (Cartesian). Blocks then combine globally via a top-level
``combine`` (default: ``combinatorial``).

**Rows-as-runs:** CSV, JSON, YAML, and NDJSON sources emit one run per
row/object by default. Use ``by_position`` when aligning multiple lists by
index, and ``combinatorial`` for Cartesian expansion within a block or across
blocks.

Schema
------

.. code-block:: yaml

   run_space:
     combine: combinatorial
     max_runs: 1000
     dry_run: false
     blocks:
       - mode: by_position
         context:
           lr: [0.001, 0.01, 0.1]
           momentum: [0.8, 0.9, 0.95]
       - mode: combinatorial
         context:
           batch_size: [8, 16]
           seed: [1, 2]

Cheat-sheet
-----------

- **Block modes**
  - ``by_position`` — index-aligned lists; index *i* travels together → one run per index.
  - ``combinatorial`` — Cartesian product over the listed keys.
- **Blocks combination**
  - ``combine: combinatorial`` *(default)* — Cartesian product across blocks.
  - ``combine: by_position`` — align blocks by index; all blocks must expand to the same size.
- **External sources**
  - Default: **rows-as-runs** for CSV/JSON/YAML/NDJSON when selecting rows/objects (no extra mode needed). Use ``by_position`` when aligning multiple lists; use ``combinatorial`` for Cartesian expansions.
- **Conflicts**
  - Duplicate context keys **across blocks** → fail fast.
  - Duplicate key **within a block** (``context`` vs ``source``) → fail fast.
- **Safety switches**
  - ``max_runs`` limits total expansions; exceeding it raises an error.
  - ``dry_run`` prints the plan (with previews) and exits without execution. See also :doc:`cli`.

Examples
--------

.. literalinclude:: ../examples/run_space/csv_rows.yaml
   :language: yaml
   :caption: docs/examples/run_space/csv_rows.yaml

.. literalinclude:: ../examples/run_space/block_combinatorial_two_sources.yaml
   :language: yaml
   :caption: docs/examples/run_space/block_combinatorial_two_sources.yaml

.. literalinclude:: ../examples/run_space/csv_columns_combinatorial.yaml
   :language: yaml
   :caption: docs/examples/run_space/csv_columns_combinatorial.yaml

External sources (rows-as-runs by default)
------------------------------------------

Blocks can read values from external files. Rows are treated as runs unless a
block explicitly requests ``mode: combinatorial`` for Cartesian expansion.

.. note::

   **Rows-as-runs by default.** CSV, JSON, YAML, and NDJSON sources interpret each
   row/object as a single run when ``mode`` is omitted or set to ``by_position``.

.. code-block:: yaml

   - mode: by_position
     source:
       format: csv | json | yaml | ndjson
       path: params/optim.csv
       select: [lr, momentum]
       rename: { momentum: mom }
       # rows are runs when mode is omitted or ``by_position``

Linkage to Pipelines
--------------------

Each ``pipeline_start`` includes foreign keys when spawned from a Run-Space launch:

- ``run_space_spec_id`` (plan identity)
- optional ``run_space_inputs_id`` (inputs snapshot)
- ``run_space_launch_id`` (launch/session)
- ``run_space_attempt`` (retry counter)

See :doc:`run_space_lifecycle` for the Run-Space lifecycle and foreign-key
relationships.

Rules
-----

* Duplicate context keys **across blocks** raise an error (fail-fast).
* Within a block, keys from ``context`` and ``source`` must be disjoint.
* ``by_position`` blocks require all lists to have identical length.
* ``combinatorial`` blocks compute the Cartesian product of their lists.
* Blocks combine via ``combine`` (``combinatorial`` or ``by_position``).
* ``max_runs`` prevents accidental explosions; ``dry_run`` prints the plan and exits.

CLI integration
---------------

``semantiva run`` exposes run-space helpers:

* ``--run-space-file`` - load a ``run_space`` block from a separate YAML file.
* ``--run-space-max-runs`` - override the safety limit on the number of runs.
* ``--run-space-dry-run`` - compute the expansion, print block sizes plus previews, and exit without executing.

SER
---

The planner returns metadata with block sizes, modes, context keys, and source
provenance (path, format, SHA-256, selectors, and renames).
Per-run metadata includes ``run_space.index``, ``run_space.total``,
``run_space.combine``, and ``run_space.context``.
