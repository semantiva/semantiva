.. _cli:

Semantiva CLI
=============

The ``semantiva`` command lets you **inspect** and **run** pipelines from the terminal.

Quick view
----------

.. code-block:: bash

   semantiva --help
   semantiva run <pipeline.yaml> [--dry-run] [--validate] [--set key=value ...] [--context key=value ...] [--trace-*] [-v|--verbose] [-q|--quiet]
   semantiva inspect <pipeline.yaml> [--extended] [-v|--verbose] [-q|--quiet]
   semantiva dev lint [--modules pkg ...] [--paths path ...] [--extensions ext ...] [--yaml file.yaml ...]

Subcommands
-----------

semantiva run
~~~~~~~~~~~~~

.. _run-options:

Execute a pipeline defined in YAML.

**Usage**

.. code-block:: bash

   semantiva run path/to/pipeline.yaml [OPTIONS]

**Options**

- ``-v`` / ``--verbose``: increase log verbosity (enables DEBUG-level logging).
- ``-q`` / ``--quiet``: reduce log verbosity (sets ERROR-level logging — errors only).
- ``--dry-run``: build the pipeline graph without executing nodes.
- ``--validate``: parse and validate configuration only.
- ``--set``: override configuration values using dotted paths (e.g., ``--set pipeline.param=value``). Can be used multiple times. Values are parsed using YAML semantics.
- ``--context key=value``: inject initial payload context. Multiple ``--context`` flags are allowed; quote lists for shells. Values are parsed using YAML semantics (for example, ``1.0`` -> float, ``true`` -> bool).
- Tracing options (see :doc:`tracing`):
   - ``--trace-driver``: e.g. ``jsonl``
   - ``--trace-output``: directory or file path
   - ``--trace-detail``: ``hash``, ``repr``, ``context``, ``all``

**Examples**

.. code-block:: bash

   # Run with verbose logging
   semantiva run hello_pipeline.yaml -v

   # Run with tracing enabled (JSONL)
   semantiva run hello_pipeline.yaml \
     --trace-driver jsonl \
     --trace-output traces/ \
     --trace-detail hash

semantiva inspect
~~~~~~~~~~~~~~~~~

Parse YAML, build the canonical graph, and run pre-execution checks.

**Usage**

.. code-block:: bash

   semantiva inspect path/to/pipeline.yaml [--extended] [OPTIONS]

**Options**

- ``--extended``: include node identities (``node_uuid``), ports, parameters, inferred types (where available).
- ``--strict``: exit non-zero if configuration contains invalid parameters.
- Verbosity: ``-v`` / ``--verbose`` and ``-q`` analogous to ``run``.

Inspection degrades gracefully for malformed configs and prints validation warnings, continuing to emit a report (see "Error-Resilient Inspection" in the CLI source).

**Examples**

.. code-block:: bash

   # Basic inspection
   semantiva inspect hello_pipeline.yaml

   # Extended inspection (identities & details)
   semantiva inspect hello_pipeline.yaml --extended

**Strict validation**

.. code-block:: bash

   semantiva inspect my_pipeline.yaml --strict

If any node contains configuration parameters that are not accepted by its processor,
the command will exit non-zero and list the offending parameters.

semantiva dev lint
~~~~~~~~~~~~~~~~~~

Run contract checks against discovered components. Use optional discovery
flags to import modules, scan paths, or load pipeline YAML files.

**Usage**

.. code-block:: bash

   semantiva dev lint [--modules pkg ...] [--paths path ...]
                      [--extensions ext ...] [--yaml pipeline.yaml ...]

**Options**

- ``--modules``: import modules before scanning.
- ``--paths``: scan Python files or packages for components.
- ``--extensions``: load Semantiva extension entry points.
- ``--yaml``: load pipeline YAMLs (ensures extensions are loaded).
- ``--export-contracts``: write the rule catalog to a Markdown file.

Exit code is non-zero when any ``SVA`` error diagnostics are emitted.

Common behaviors
----------------

Exit codes
~~~~~~~~~~

- **0** — success.
- **1** — CLI argument error.
- **2** — file not found.
- **3** — configuration or validation error.
- **4** — runtime execution error.
- **5** — keyboard interrupt.
- **non-zero** — a validation or runtime error occurred; see stderr for details.

Error surface
~~~~~~~~~~~~~

- ``inspect``: reports spec-phase issues (unknown processor, bad ports, missing params).
  Non-zero exit code; details printed to stderr.
- ``run``: may fail during initialization (imports/params) or at execution time
  (type contracts). Non-zero exit code; failing node identity appears in the message
  when available (``node_uuid``). See :doc:`introspection_validation`.

Logs & verbosity
~~~~~~~~~~~~~~~~

- ``-q`` sets ERROR-level logging (errors only).
- ``-v`` enables DEBUG-level logging.
- By default the CLI runs at INFO level.

By default, logs are written to stderr; configure handlers in your ``logging`` policy.
See :doc:`logger` for examples.

Tracing shortcuts
~~~~~~~~~~~~~~~~~

All tracing flags are shared between ``run`` and the underlying execution.
See :doc:`tracing` for the driver matrix, detail flags, and output format.

.. seealso::

   Tracing options: see :ref:`trace-detail-and-format` and :ref:`pretty-vs-compact-json`
   for driver selection, detail flags, and output naming.

Ecosystem
---------

- Visualize a pipeline diagram with **Semantiva Studio Viewer**:
  see :doc:`studio_viewer` (``semantiva-studio-viewer serve-pipeline ...``).
- If you use domain extensions (e.g., **Semantiva Imaging**), their processors
  are referenced the same way in YAML (by class name or registry name).

Recipes
-------

Run with verbose logs
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   semantiva run hello_pipeline.yaml -v
   
   # Alternative: direct Python execution
   python -m semantiva.semantiva run hello_pipeline.yaml -v

Inspect with identities (pre-flight)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   semantiva inspect hello_pipeline.yaml --extended

Run with JSONL tracing (hash summaries)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   semantiva run hello_pipeline.yaml \
     --trace-driver jsonl \
     --trace-output traces/ \
     --trace-detail hash

Override configuration values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Override pipeline parameters
   semantiva run hello_pipeline.yaml --set pipeline.nodes.0.parameters.value=5.0
   
   # Multiple overrides
   semantiva run hello_pipeline.yaml \
     --set pipeline.nodes.0.parameters.value=5.0 \
     --set pipeline.nodes.1.parameters.factor=3.0

Minimal failure demonstration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Intentionally mis-configure to see validation errors
   semantiva inspect examples/broken_pipeline.yaml --extended || echo "non-zero exit as expected"

FAQ
---

**Q:** ``semantiva: command not found``  
**A:** Ensure your Python environment is active and Semantiva is installed:
``pip install semantiva``. If using a venv, activate it before running.

**Q:** ImportError for my custom processor  
**A:** Install your package into the same environment so it’s importable.

**Q:** My trace file is empty  
**A:** Re-run with ``--trace-driver jsonl --trace-output <dir>`` and
check :doc:`tracing` for detail flags and file naming.

