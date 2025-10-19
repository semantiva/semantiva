Run Space Quickstart (Local)
============================

This example shows how to execute the same pipeline multiple times with
different context values using the **run space** planner.

What you'll run
---------------

For each combination of ``value`` and ``factor``:

1. **FloatValueDataSource** emits ``value``.
2. **FloatAddOperation** adds a constant ``addend`` (``1.0``) bound from the run
   context.
3. **FloatMultiplyOperation** multiplies by ``factor`` (also bound from context).
4. **FloatCollectValueProbe** captures the computed float into the context under
   ``result`` so it can be used downstream.
5. A template context factory creates a filename using the run-space
   values and the computed ``result``.
6. **FloatTxtFileSaver** writes the result to disk; one file is produced per run.

Notes and rationale
-------------------

- Run space blocks materialize **context**, not node parameters. Nodes read
  values via ``${...}`` expressions, keeping the ontology consistent.
- The example uses a single ``by_position`` block that pairs ``value``, ``addend``
  and ``factor`` lock-step. Additional blocks could add seeds, augmentations, or
  any other context dimensions.
- The default local orchestrator runs jobs serially. The JSONL trace driver pins
  ``run_space.*`` metadata (index, total, combine mode, and per-run context) so
  runs can be replayed or audited later.

YAML
----

.. literalinclude:: ../examples/run_space_floats.yaml
   :language: yaml
   :caption: docs/source/examples/run_space_floats.yaml

Key ideas
---------

- ``by_position`` block: the lists under ``context`` must be the same length; each
  index becomes one run. ``combinatorial`` blocks compute full Cartesian products.
- Parameter resolution from context: processors receive ``value``, ``addend``
  and ``factor`` via the run context without redefining their parameter blocks.
- SER provenance: each run records ``run_space.index`` and ``run_space.context``
  inside ``assertions.args`` along with full block metadata for auditability.

Next steps
----------

- To experiment with combinatorial sweeps, add a second block with
  ``mode: combinatorial`` (for example seeds or augmentations).
- To plan without executing, set ``run_space.dry_run: true`` or pass
  ``--run-space-dry-run`` to :command:`semantiva run`.
- To run remotely, add an ``execution`` block selecting the desired orchestrator
  (see :doc:`../architecture/pipeline_schema`).
