.. _trace_aggregator_v1:

Trace Aggregator v1
===================

The Trace Aggregator groups Semantiva Trace Stream records into **per-run** and **per-launch** aggregates and computes **completeness**.

.. important::
   **Current scope is in-memory only.**
   The aggregator accepts **Python dictionaries** representing validated trace records.
   **No IO/exporters** (JSONL readers/writers, SQLite/DuckDB, or CLI wiring) are implemented.

Motivation
----------
The aggregator centralizes semantics previously duplicated in viewer-side code. It produces deterministic
aggregates and a canonical completeness report so downstream tools (e.g. :ref:`Trace Stream v1 <trace_stream_v1>`,
:ref:`glossary`) remain aligned.

Record Types (input)
--------------------
The aggregator accepts any mixture of the following record types:

- ``run_space_start``, ``run_space_end``
- ``pipeline_start``, ``pipeline_end``
- ``ser`` (Semantic Execution Record)

See :ref:`trace_stream_v1` for schema details and registry.

Aggregation Model
-----------------
Two levels:

**Per-Run (RunAggregate)**

* Key: ``run_id``
* Collects: one ``pipeline_start`` (optional), zero or more ``ser``, one ``pipeline_end`` (optional)
* Computes:
  - status: ``complete`` | ``partial`` | ``invalid``
  - problems: ``missing_pipeline_start``, ``missing_pipeline_end``, ``start_ts_gt_end_ts``
  - coverage vs. ``pipeline_spec_canonical.nodes[*].node_uuid``
  - node metrics (counts by status, last timing/error)

**Per-Launch (LaunchAggregate)**

* Key: ``(run_space_launch_id, run_space_attempt)``
* Collects: one ``run_space_start`` (optional), one ``run_space_end`` (optional), and the list of attached ``run_id`` values
* Computes:
  - status: ``complete`` | ``partial`` | ``invalid``
  - problems: ``missing_run_space_start``, ``missing_run_space_end``
  - rollup by run status

Public API
----------
The **only** public methods are:

- ``TraceAggregator.ingest(record: dict) -> None``
- ``TraceAggregator.ingest_many(records: Iterable[dict]) -> None``
- ``TraceAggregator.get_run(run_id: str) -> Optional[RunAggregate]``
- ``TraceAggregator.iter_runs() -> Iterable[RunAggregate]``
- ``TraceAggregator.get_launch(launch_id: str, attempt: int) -> Optional[LaunchAggregate]``
- ``TraceAggregator.iter_launches() -> Iterable[LaunchAggregate]``
- ``TraceAggregator.finalize_run(run_id: str) -> RunCompleteness``
- ``TraceAggregator.finalize_launch(launch_id: str, attempt: int) -> LaunchCompleteness``
- ``TraceAggregator.finalize_all() -> (list[RunCompleteness], list[LaunchCompleteness])``

.. note::
   All other helpers are private (underscore-prefixed) and considered implementation details.

Usage (dict-only)
-----------------
.. code-block:: python

   from semantiva.trace.aggregation.aggregator import TraceAggregator

   aggregator = TraceAggregator()
   # Run-Space lifecycle (optional)
   aggregator.ingest({"record_type": "run_space_start", "run_space_launch_id": "L1", "run_space_attempt": 1})

   # Run lifecycle + node events
   aggregator.ingest({"record_type": "pipeline_start", "run_id": "R1", "pipeline_id": "P",
                      "run_space_launch_id": "L1", "run_space_attempt": 1,
                      "pipeline_spec_canonical": {"nodes": [{"node_uuid": "n1"}]}})
   aggregator.ingest({"record_type": "ser", "identity": {"run_id": "R1", "pipeline_id": "P", "node_id": "n1"},
                      "status": "succeeded", "timing": {"wall_ms": 1}})
   aggregator.ingest({"record_type": "pipeline_end", "run_id": "R1"})

   # Close the launch
   aggregator.ingest({"record_type": "run_space_end", "run_space_launch_id": "L1", "run_space_attempt": 1})

   run_report = aggregator.finalize_run("R1")
   launch_report = aggregator.finalize_launch("L1", 1)

Completeness & Issues
---------------------
**Run status**
- ``complete``: saw both ``pipeline_start`` and ``pipeline_end``
- ``partial``: only one lifecycle edge, or nodes present with a missing edge
- ``invalid``: no lifecycle and no nodes, or structural contradictions

**Run problems**
- ``missing_pipeline_start``
- ``missing_pipeline_end``
- ``start_ts_gt_end_ts``

**Launch problems**
- ``missing_run_space_start``
- ``missing_run_space_end``

**Terminal node statuses**
- ``succeeded``, ``error``, ``skipped``, ``cancelled``

Cross-References
----------------
- Trace Stream schemas: :ref:`trace_stream_v1`
- Terminology: :ref:`glossary`
