Semantiva CLI
=============

.. note::
   **Single Source of Truth (SSoT)** — This page mirrors the CLI implementation at
   ``semantiva/cli/__init__.py``. Update code and docs together to avoid drift.

Overview
--------
- ``semantiva run``  — Execute a pipeline from YAML.
- ``semantiva inspect``  — Inspect a pipeline configuration.
- ``semantiva dev lint`` — Lint components against contracts.

Exit Codes
----------
0: success, 1: CLI error, 2: file error, 3: config error, 4: runtime error, 5: interrupt.

Run
---
Execute a pipeline.

**Syntax**

.. code-block:: text

    semantiva run PIPELINE.yaml
                      [--dry-run]
                      [--validate]
                      [--set key=value]...
                      [--context key=value]...
                      [-v | --verbose]
                      [-q | --quiet]
                      [--execution.orchestrator CLASS]
                      [--execution.executor CLASS]
                      [--execution.transport CLASS]
                      [--execution.option key=value]...
                      [--trace.driver NAME]
                      [--trace.output PATH-or-DriverSpec]
                      [--trace.option key=value]...
                      [--fanout.param NAME]
                      [--fanout.values SEQ]
                      [--fanout.values-file PATH]
                      [--fanout.multi NAME=SEQ]...
                      [--fanout.multi-file PATH]
                      [--version]

**Arguments**
- ``PIPELINE.yaml``            Path to the pipeline YAML file.
- ``--dry-run``                Build graph without executing nodes.
- ``--validate``               Validate configuration only.
- ``--set key=value``          Override by dotted path (lists use numeric indices).

  - Value parsing: YAML first; falls back to string on parse error.

- ``--context key=value``      Inject initial context key/values.

  - Value parsing: YAML first; falls back to string on parse error.

- ``-v / --verbose``           Increase log verbosity.
- ``-q / --quiet``             Only show errors.
- ``--execution.orchestrator`` Resolve orchestrator via the Execution Component Registry (ECR).
- ``--execution.executor``     Resolve executor via the Execution Component Registry (ECR).
- ``--execution.transport``    Resolve transport via the Execution Component Registry (ECR).
- ``--execution.option``       Key/value pairs forwarded to the orchestrator ``options``.
- ``--trace.driver``           Trace driver name (``none``, ``jsonl``, ``pythonpath``, or registry class).
- ``--trace.output``           Trace output path or ``module:Class`` when ``driver=pythonpath``.
- ``--trace.option``           Additional driver keyword arguments (repeatable).
- ``--fanout.param``           Single-parameter fan-out target name.
- ``--fanout.values``          Values for single-parameter fan-out (JSON list or comma-separated).
- ``--fanout.values-file``     External JSON/YAML file supplying fan-out values.
- ``--fanout.multi``           Multi-parameter ZIP values (repeatable ``name=[...]`` arguments).
- ``--fanout.multi-file``      External JSON/YAML mapping supplying multi fan-out values.
- ``--version``                Show CLI version.

CLI flags mirror the YAML schema. Any value provided on the command line
overrides the matching YAML block before validation and execution. Trace detail
flags are supplied via ``--trace.option detail=...`` (``hash`` is implied when no
detail is provided). Environment pins and why-ok invariants are always
captured by :py:class:`~semantiva.execution.orchestrator.orchestrator.SemantivaOrchestrator`,
ensuring consistent SER output across orchestrator implementations.

.. note::
  In YAML, use the plural key ``options`` under ``trace`` and ``execution``. The
  CLI uses repeatable singular flags ``--trace.option`` and ``--execution.option``
  to populate those mappings.

**Component Resolution**
The CLI loads extensions before constructing execution components so that the
Execution Component Registry (ECR) contains all orchestrators, executors, and
transports. Built-in identifiers include ``local`` (orchestrator), ``sequential``
(executor), and ``in_memory`` (transport). Unknown component names result in an
error with ``did-you-mean`` suggestions based on the registered inventory.

**YAML Extension Loading**
If your YAML contains:

.. code-block:: yaml

    extensions: ["my_package.ext"]

or:

.. code-block:: yaml

    pipeline:
      extensions: ["my_package.ext"]

those extensions are loaded before validation/execution. Extension registration
is deterministic and idempotent: each extension is imported once and must expose
either an entry point under ``semantiva.extensions`` or a module-level
``register()`` hook.

Inspect
-------

**Syntax**

.. code-block:: text

    semantiva inspect PIPELINE.yaml
                        [--extended]
                        [-v | --verbose]
                        [-q | --quiet]
                        [--strict]
                        [--version]

**Arguments**
- ``PIPELINE.yaml``  Path to the pipeline YAML file.
- ``--extended``     Show extended inspection details.
- ``-v / --verbose`` Increase log verbosity.
- ``-q / --quiet``   Only show errors.
- ``--strict``       Exit non-zero if configuration is invalid.
- ``--version``      Show CLI version.

Dev / Lint
----------

**Syntax**

.. code-block:: text

    semantiva dev lint
      [--modules MOD ...]
      [--paths PATH ...]
      [--extensions NAME ...]
      [--yaml FILE ...]
      [--export-contracts PATH]
      [--debug]
      [--version]

**Arguments**
- ``--modules``          Python modules to import and validate
- ``--paths``            Paths to scan for Python components
- ``--extensions``       Extension names (entry points or module names) to load and validate
- ``--yaml``             Pipeline YAML files (discovers referenced components)
- ``--export-contracts`` Write rule catalog to PATH (Markdown)
- ``--debug``            Detailed rule-by-rule diagnostics
- ``--version``          Show CLI version
