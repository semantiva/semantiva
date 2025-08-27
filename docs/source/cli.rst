.. _cli:

Semantiva CLI
=============

The ``semantiva`` command lets you **inspect** and **run** pipelines from the terminal.

Quick view
----------

.. code-block:: bash

   semantiva --help
   semantiva run <pipeline.yaml> [OPTIONS]
   semantiva inspect <pipeline.yaml> [--extended] [OPTIONS]

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
- ``--context``: inject initial payload context as one or more ``key=value`` pairs. Values are parsed using YAML semantics (for example, ``1.0`` -> float, ``true`` -> bool). This option may be repeated to supply multiple keys.
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
- Verbosity: ``-v`` / ``--verbose`` and ``-q`` analogous to ``run``.

**Examples**

.. code-block:: bash

   # Basic inspection
   semantiva inspect hello_pipeline.yaml

   # Extended inspection (identities & details)
   semantiva inspect hello_pipeline.yaml --extended

Common behaviors
----------------

Exit codes
~~~~~~~~~~

- **0** — success.
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

Planned: context injection
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   A ``--context key=value`` option may be added in a future release for
   initializing the payload context from the CLI. Until it lands, set
   initial context via your pipeline definition or programmatic API.

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


