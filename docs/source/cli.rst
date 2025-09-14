Semantiva CLI
=============
(SSoT) This page mirrors `semantiva/cli.py`. Update this doc if CLI changes.

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
                      [--trace-driver {none,jsonl,pythonpath}]
                      [--trace-output PATH-or-DriverSpec]
                     [--trace-detail FLAGS]
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
- ``--trace-driver``           ``none`` (default), ``jsonl``, or ``pythonpath``.
- ``--trace-output``           For ``jsonl``, a file path; for ``pythonpath``, a driver spec
  (``package.module:ClassName``) instantiated with no args.
- ``--trace-detail``           Comma-separated flags: ``hash, repr, context, all``
  (default: ``hash``).
- ``--version``                Show CLI version.

**YAML Extension Loading**
If your YAML contains:

.. code-block:: yaml

    extensions: ["my_package.ext"]

or:

.. code-block:: yaml

    pipeline:
      extensions: ["my_package.ext"]

those extensions are loaded before validation/execution (entry point or module import).

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
