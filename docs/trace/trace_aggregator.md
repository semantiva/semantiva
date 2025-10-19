# Core Trace Aggregator

The Semantiva trace aggregator operates entirely in-memory and accepts dictionaries that conform to the JSON Schema definitions
published under ``semantiva/trace/schema``. The aggregator is order-agnostic and run-space aware, meaning it groups pipelines per
``run_id`` and attaches them to launches identified by ``(run_space_launch_id, run_space_attempt)``.

## Public API

The :class:`~semantiva.trace.aggregation.aggregator.TraceAggregator` exposes a small surface that mirrors the lifecycle of trace
records and the completeness reporting required by downstream tooling.

- ``ingest(record: dict)``
- ``ingest_many(records: Iterable[dict])``
- ``get_run(run_id)`` and ``iter_runs()``
- ``get_launch(launch_id, attempt)`` and ``iter_launches()``
- ``finalize_run(run_id) -> RunCompleteness``
- ``finalize_launch(launch_id, attempt) -> LaunchCompleteness``
- ``finalize_all() -> Tuple[List[RunCompleteness], List[LaunchCompleteness]]``

## Notes

- Records may be ingested in any order. Start/end events and node records are correlated purely by identifiers.
- SER node completeness relies on terminal statuses in ``{"succeeded", "error", "skipped", "cancelled"}``.
- Launch completeness aggregates run statuses, surfaces missing start/end events, and
  reports a partial launch whenever any attached run is incomplete.
- No IO adapters are provided; callers are responsible for feeding Python dictionaries.
