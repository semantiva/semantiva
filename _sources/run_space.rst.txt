Run Space (v1): blocks that expand context
==========================================

A **run-space** describes a *family of runs* for a single pipeline. Instead of
manually looping over ``semantiva run`` with different ``--context`` values,
you declare the combinations once in YAML.

Conceptually:

- The pipeline definition stays the same.
- The run-space expands into individual runs, each with a concrete context.
- The run-space and each run have stable identities that appear in the trace
  stream and viewer.

From repeated CLI calls to run-space
------------------------------------

Without run-space, you might write:

.. code-block:: bash

   semantiva run hello.yaml --context value=1.0 factor=10.0 addend=1.0
   semantiva run hello.yaml --context value=2.0 factor=20.0 addend=1.0
   semantiva run hello.yaml --context value=3.5 factor=30.0 addend=1.0

With run-space, you express the same idea in YAML:

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

   pipeline:
     # your nodes here

Key fields
----------

- ``combine`` – how to combine blocks (for example ``by_position`` or
  ``combinatorial``).
- ``max_runs`` – hard safety cap to avoid accidental explosion of runs.
- ``dry_run`` – when ``true``, Semantiva will expand the plan and print it
  without executing the pipeline.
- ``blocks`` – a list of blocks, each with a ``mode`` and a ``context``
  mapping.

See :doc:`tutorials/run_space_quickstart` for more complete examples.

Identity and traceability
-------------------------

Each run-space has:

- A **run-space configuration ID** – derived from the run-space section itself.
- A **run-space launch ID** – derived from the configuration plus launch
  parameters.

Each expanded run has:

- A **run ID** – part of the Semantic Execution Record (SER) identity block.
- A link back to both the pipeline configuration and the run-space
  configuration.

These IDs are documented in :doc:`identity_cheatsheet` and appear in:

- :doc:`ser`
- :doc:`trace_stream_v1`
- :doc:`trace_aggregator_v1`
- :doc:`run_space_emission`
- :doc:`run_space_lifecycle`

External sources
----------------

Run-space blocks can also pull values from external sources such as CSV files.
Those patterns are more advanced and are covered in
:doc:`tutorials/run_space_quickstart`.

For local, single-machine experiments, the YAML-only form is often sufficient
and keeps the configuration self-contained.
