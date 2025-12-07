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

- ``0`` - Success.
- ``1`` - CLI usage error.
- ``2`` - File error (missing or unreadable files).
- ``3`` - Configuration error (invalid YAML or contract violations).
- ``4`` - Runtime error during execution.
- ``5`` - Interrupted by user.

Run - execute a pipeline
------------------------

Minimal usage:

.. code-block:: bash

   semantiva run PIPELINE.yaml

Common options:

- ``--context key=value`` - Provide initial context key/values.
- ``--run-space-override path.yaml`` - Override the ``run_space`` block.
- ``--dry-run`` - Build the graph without executing nodes.
- ``--validate`` - Validate configuration only.

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

Inspect - pre-flight checks & identities
----------------------------------------

See :doc:`introspection_validation` for details. From the CLI:

.. code-block:: bash

   # Basic inspection
   semantiva inspect pipeline.yaml

   # Extended report with per-node details
   semantiva inspect pipeline.yaml --extended

Developer tools - dev lint
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

.. code-block:: console

   usage: semantiva run [-h] [--dry-run] [--validate] [--set key=value] [--context key=value] [-v] [-q]
                        [--execution.orchestrator EXEC_ORCHESTRATOR] [--execution.executor EXEC_EXECUTOR]
                        [--execution.transport EXEC_TRANSPORT] [--execution.option key=value]
                        [--trace.driver TRACE_DRIVER] [--trace.output TRACE_OUTPUT] [--trace.option key=value]
                        [--run-space-file RUN_SPACE_FILE] [--run-space-max-runs RUN_SPACE_MAX_RUNS]
                        [--run-space-dry-run] [--run-space-launch-id RUN_SPACE_LAUNCH_ID]
                        [--run-space-idempotency-key RUN_SPACE_IDEMPOTENCY_KEY]
                        [--run-space-attempt RUN_SPACE_ATTEMPT] [--version]
                        pipeline

   positional arguments:
     pipeline              Path to the pipeline YAML file

   options:
     -h, --help            show this help message and exit
     --dry-run             Build graph without executing nodes
     --validate            Validate configuration only
     --set key=value       Override configuration values (dotted paths)
     --context key=value   Inject context key-value pairs
     -v, --verbose         Increase log verbosity
     -q, --quiet           Only show errors
     --execution.orchestrator EXEC_ORCHESTRATOR
                           Orchestrator class name to resolve via the registry
     --execution.executor EXEC_EXECUTOR
                           Executor class name to resolve via the registry
     --execution.transport EXEC_TRANSPORT
                           Transport class name to resolve via the registry
     --execution.option key=value
                           Additional execution option (repeatable)
     --trace.driver TRACE_DRIVER
                           Trace driver name ('jsonl', default JSONL trace driver)
     --trace.output TRACE_OUTPUT
                           Trace output path for the JSONL driver
     --trace.option key=value
                           Trace driver option (repeatable)
     --run-space-file RUN_SPACE_FILE
                           Path to a YAML file containing a run_space block
     --run-space-max-runs RUN_SPACE_MAX_RUNS
                           Override run_space.max_runs safety limit
     --run-space-dry-run   Plan run_space expansions, print summary with previews, and exit
     --run-space-launch-id RUN_SPACE_LAUNCH_ID
                           Explicit run_space_launch_id to reuse for this execution
     --run-space-idempotency-key RUN_SPACE_IDEMPOTENCY_KEY
                           Derive run_space_launch_id deterministically from spec/inputs
     --run-space-attempt RUN_SPACE_ATTEMPT
                           Attempt counter for the run-space launch (default: 1)
     --version             show program's version number and exit

.. code-block:: bash

   semantiva inspect --help

.. code-block:: console

   usage: semantiva inspect [-h] [--extended] [-v] [-q] [--strict] [--version] pipeline

   Analyze pipeline configuration and display identity information. Shows semantic ID, config ID, run-space config
   ID, and required context keys. Use --extended to see per-node details including sweep parameters.

   positional arguments:
     pipeline       Path to the pipeline YAML file

   options:
     -h, --help     show this help message and exit
     --extended     Show extended report with per-node details and sweep summaries
     -v, --verbose  Increase log verbosity
     -q, --quiet    Only show errors
     --strict       Exit non-zero if configuration contains invalid parameters
     --version      show program's version number and exit

.. code-block:: bash

   semantiva dev lint --help
