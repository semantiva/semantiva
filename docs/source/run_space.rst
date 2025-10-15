Run Space (v1): blocks that expand context
==========================================

Semantiva's run space defines a set of executions by expanding **context** keys.
Each *block* expands its own keys using either ``zip`` (lock-step) or
``product`` (Cartesian). Blocks then combine globally via a top-level
``combine`` (default: ``product``).

Schema
------

.. code-block:: yaml

   run_space:
     combine: product
     max_runs: 1000
     dry_run: false
     blocks:
       - mode: zip
         context:
           lr: [0.001, 0.01, 0.1]
           momentum: [0.8, 0.9, 0.95]
       - mode: product
         context:
           batch_size: [8, 16, 32, 64]
           aug: [weak, strong]
           seed: [1, 2]

Cheat-sheet
-----------

- **Block modes**
  - ``zip`` - lock-step lists; index *i* travels together, producing one run per index.
  - ``product`` - Cartesian product over the listed keys.
- **Blocks combination**
  - ``combine: product`` *(default)* - Cartesian product across blocks.
  - ``combine: zip`` - zip blocks together; all blocks must expand to the same size.
- **External sources**
  - Default: **rows-as-runs** (``source.mode: zip``) for CSV/JSON/YAML/NDJSON files.
  - Use ``source.mode: product`` when the file stores a mapping of lists.
- **Conflicts**
  - Duplicate context keys **across blocks** → fail fast.
  - Duplicate key **within a block** (``context`` vs ``source``) → fail fast.
- **Safety switches**
  - ``max_runs`` limits total expansions; exceeding it raises an error.
  - ``dry_run`` prints the plan (with previews) and exits without execution. See also :doc:`cli`.

External sources (rows-as-runs by default)
------------------------------------------

Blocks can read values from external files. Rows are treated as runs unless
``source.mode: product`` is specified.

.. note::

   **Rows-as-runs by default.** CSV, JSON, YAML, and NDJSON sources interpret each
   row/object as a single run when ``source.mode`` is omitted (defaults to ``zip``).

.. code-block:: yaml

   - mode: zip
     source:
       format: csv | json | yaml | ndjson
       path: params/optim.csv
       select: [lr, momentum]
       rename: { momentum: mom }
       mode: zip  # default; rows are runs

Rules
-----

* Duplicate context keys **across blocks** raise an error (fail-fast).
* Within a block, keys from ``context`` and ``source`` must be disjoint.
* ``zip`` blocks require all lists to have identical length.
* ``product`` blocks compute the Cartesian product of their lists.
* Blocks combine via ``combine`` (``product`` or ``zip``).
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
provenance (path, format, SHA-256, selectors, renames, and per-source mode).
Per-run metadata includes ``run_space.index``, ``run_space.total``,
``run_space.combine``, and ``run_space.context``.
