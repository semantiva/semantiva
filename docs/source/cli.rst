Semantiva CLI
=============

The CLI is the main entry point for executing pipelines, inspecting
configurations and running developer tools.

Overview
--------

Subcommands:

- ``semantiva run``  — Execute a pipeline from YAML.
- ``semantiva inspect``  — Inspect a pipeline configuration.
- ``semantiva dev lint`` — Lint components against contracts.

Exit codes
----------

- ``0`` – Success.
- ``1`` – CLI usage error.
- ``2`` – File error (missing or unreadable files).
- ``3`` – Configuration error (invalid YAML or contract violations).
- ``4`` – Runtime error during execution.
- ``5`` – Interrupted by user.

Run – execute a pipeline
------------------------

Minimal usage:

.. code-block:: bash

   semantiva run PIPELINE.yaml

Common options:

- ``--context key=value`` – Provide initial context key/values.
- ``--run-space-override path.yaml`` – Override the ``run_space`` block.
- ``--dry-run`` – Build the graph without executing nodes.
- ``--validate`` – Validate configuration only.

``--context`` vs ``--set``
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to influence a run from the command line:

- ``--context key=value``

  - Writes into the **context channel**.
  - Typical for values that conceptually belong to the run (experiment IDs,
    seeds, ranges, file paths and so on).
  - Values are parsed as YAML first, then treated as strings on parse error.

- ``--set dotted.path=value``

  - Overrides a key *inside the pipeline configuration*.
  - Uses dotted paths to navigate the YAML structure (lists use numeric indices).
  - Intended for advanced and debug scenarios where you need an ad-hoc tweak
    without editing the YAML file.
  - Values are also parsed as YAML.

For most day-to-day use, prefer ``--context``. Use ``--set`` when you explicitly
want to change the configuration itself.

Inspect – pre-flight checks & identities
----------------------------------------

See :doc:`introspection_validation` for details. From the CLI:

.. code-block:: bash

   # Basic inspection
   semantiva inspect pipeline.yaml

   # Extended report with per-node details
   semantiva inspect pipeline.yaml --extended

Developer tools – dev lint
--------------------------

The ``dev`` subcommand hosts developer-oriented tools. Currently:

.. code-block:: bash

   semantiva dev lint

This command scans registered components and validates them against the
Semantiva contracts. It reports issues with stable ``SVA`` codes. See
:doc:`contracts` for details.

Full options
------------

Run ``--help`` on each subcommand for the authoritative list of options and
flags:

.. code-block:: bash

   semantiva run --help
   semantiva inspect --help
   semantiva dev lint --help
