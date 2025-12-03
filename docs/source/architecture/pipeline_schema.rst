Pipeline Configuration Schema
=============================

.. admonition:: Level 300 (Advanced)

   This page is advanced reference material intended for **architects and
   integrators**. You should be comfortable with pipelines and basic
   inspection before reading this (see :doc:`../personas/pipeline_users` and
   :doc:`../personas/architects_system_designers`).

Semantiva pipeline YAML has a small set of **top-level sections** that work
together:

1. ``extensions`` - which Python packages/extensions to load.
2. ``pipeline`` - the node graph and its configuration.
3. ``run_space`` - optional description of multiple runs for a single pipeline.
4. ``trace`` - trace driver configuration.
5. ``execution`` - orchestration/executor configuration.

This page describes the expected shape of each section with an emphasis on
validation behaviour.

Extensions
----------

Extensions are imported before the pipeline graph is built so that their
processors, data types, and trace drivers are registered.

.. code-block:: yaml

   extensions:
     - "semantiva-imaging"
     - "my_package.my_semantiva_extension"

- Must be a list of importable module paths.
- The list is ordered; later extensions can register additional components or
  override names, depending on the registry implementation.

Pipeline
--------

The ``pipeline`` block contains the node graph and optional pipeline-level
configuration:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: MySource
         parameters:
           ...

       - processor: MyOperation
         parameters:
           ...

Each node entry is validated according to the processor contracts (see
:doc:`../creating_components`). At minimum, a node declares a processor and,
optionally, a parameters mapping.

Node definition schema
----------------------

Common node keys include:

- ``processor`` (required): fully qualified class name or a registered short name.
- ``parameters`` (optional): mapping of parameters to be resolved at runtime.
- ``derive`` (optional): preprocessor boundary with tools such as
  ``parameter_sweep`` (see :doc:`../collection_modifiers`).
- ``ports`` (optional): explicit port wiring when the defaults are not sufficient.

The loader enforces that ``parameters`` is a mapping when present, and that
derived tools receive the correct shape.

Run-space schema
----------------

The optional ``run_space`` section describes **families of runs** using context
combinations. A minimal example:

.. code-block:: yaml

   run_space:
     combine: combinatorial
     max_runs: 20
     dry_run: false
     blocks:
       - mode: by_position
         context:
           value:  [1.0, 2.0, 3.5]
           factor: [10.0, 20.0, 30.0]
           addend: [1.0, 1.0, 1.0]

Top-level keys:

- ``combine``: expansion strategy (for example ``by_position`` or
  ``combinatorial``).
- ``max_runs``: upper bound on expanded runs for safety.
- ``dry_run``: when true, expand but do not execute.
- ``blocks``: list of blocks with a ``mode`` and a ``context`` mapping.

See :doc:`../run_space` and :doc:`../tutorials/run_space_quickstart` for details.

Trace driver configuration (``trace``)
--------------------------------------

The ``trace`` block configures how Semantic Execution Records (SER) are written:

.. code-block:: yaml

   trace:
     driver: "jsonl"
     output_path: "traces/"
     detail: "hash"

Fields:

- ``driver`` (required): registered driver name, e.g. ``"jsonl"`` or ``"none"``.
- ``output_path`` (optional): directory or file path. For JSONL, a timestamped
  ``*.ser.jsonl`` file is created when a directory is given.
- ``detail`` (optional): one of:

  - ``hash`` (default): SHA-256 digests only.
  - ``repr``: also include ``repr`` for input/output data.
  - ``context``: with ``repr``, also include ``repr`` for pre/post context.
  - ``all``: enable ``hash`` + ``repr`` + ``context``.

- ``options`` (optional): additional driver keyword arguments (must be a mapping).

Validation rules:

- ``trace.options`` must be a mapping when present.
- Singular ``option`` keys are invalid and will produce a clear error.

See :doc:`../trace_stream_v1` and :doc:`../ser` for the runtime record format.

Execution configuration (``execution``)
---------------------------------------

The optional ``execution`` block configures how a pipeline is orchestrated and
executed. When omitted, Semantiva uses the default single-machine configuration
shown below, which is well suited for development and small-scale runs on a
single host:

.. code-block:: yaml

   execution:
     orchestrator: LocalSemantivaOrchestrator
     executor: SequentialSemantivaExecutor
     transport: InMemorySemantivaTransport
     options: {}

Fields:

- ``orchestrator``: orchestrator class or registered name.
- ``executor``: executor class or registered name.
- ``transport``: transport class or registered name.
- ``options`` (optional): mapping of additional execution options.

Validation rules:

- ``execution.options`` must be a mapping.
- ``option`` (singular) is not accepted; only ``options`` is valid.

These shapes mirror the CLI flags documented in :doc:`../cli` and are exercised
in the runnable examples under :doc:`../examples_index`.

For an overview of the execution layer and default components see
:doc:`../execution`.
