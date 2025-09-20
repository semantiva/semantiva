Fan-Out Quickstart (Local)
==========================

This example shows how to run the same pipeline multiple times with different
parameters (fan-out) using the built-in Float demo processors.

What you'll run
---------------

For each (``value``, ``factor``) pair:

1. **FloatValueDataSource** emits ``value``.
2. **FloatAddOperation** adds a constant ``addend`` (``1.0``).
3. **FloatMultiplyOperation** multiplies by ``factor``.
4. **FloatCollectValueProbe** captures the computed float into the context under the key ``result`` (this mirrors the pipeline's inspected output so it can be used downstream).
5. A string builder context factory creates a filename using all fan-out inputs and the computed ``result`` (pattern: ``{value}_plus_{addend}_times_{factor}_equals_{result}.txt``). That filename is placed into the context as a path for the saver.
6. **FloatTxtFileSaver** reads the path from the context and writes the textual result to disk; one file is produced per fan-out run.

Notes and rationale
- Multi-parameter ZIP fan-out: the ``multi`` block now supplies three lists (``value``, ``addend``, ``factor``). The engine zips them and runs one pipeline per index; equal lengths are enforced.
- Supplying parameters via context: the demo processors do not declare these parameters explicitly — the fan-out injects ``value``, ``addend`` and ``factor`` into the run context and processors pick them up automatically. This lets you vary any number of parameters without changing node parameter blocks.
- Filename building: using a stringbuild context factory (registered as a context-producing processor) lets you assemble filenames/IDs from runtime values cleanly and portably.
- Execution and tracing: the default local orchestrator runs jobs serially. The trace driver (`jsonl`) writes a SER file under ``./ser/`` containing per-run pinned arguments (e.g., fanout index and the values used) so runs can be inspected or replayed later.
The final result is: ``(value + 1.0) x factor``.

YAML
----

.. literalinclude:: ../examples/fanout_floats.yaml
   :language: yaml
   :caption: docs/source/examples/fanout_floats.yaml

Key ideas
---------

- Fan-out (ZIP): the ``multi`` block provides two lists of equal length
  (``value`` and ``factor``). The engine creates one run per index.
- Parameter resolution from context: the nodes do not declare ``value`` or
  ``factor`` in their parameters; these are injected into the context by
  fan-out and picked up automatically by the processors.
- Local execution: no ``execution:`` block is needed; the default local
  orchestrator runs each job serially.
- SER: A JSONL file is written into the ``./ser/`` directory — the trace driver creates one JSONL file per pipeline run (one file per fan-out job) containing per-run pinned arguments (e.g. ``fanout.index``, ``fanout.values``).

Next steps
----------

- To run on Ray, add an ``execution:`` block selecting the registered Ray
  orchestrator/executor/transport (see :doc:`../architecture/pipeline_schema`).
- To build filenames or IDs from fan-out values, use the string builder
  context factory (see :doc:`../context_processors`).
