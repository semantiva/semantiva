# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Core run-space aware trace aggregation."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, cast

from .models import (
    LaunchAggregate,
    LaunchCompleteness,
    NodeAggregate,
    RunAggregate,
    RunCompleteness,
)

_TERMINAL = {"succeeded", "error", "skipped", "cancelled"}


class TraceAggregator:
    """Public API for Semantiva core trace aggregation."""

    def __init__(self) -> None:
        self._runs: Dict[str, RunAggregate] = {}
        self._launches: Dict[Tuple[str, int], LaunchAggregate] = {}

    # ---- lifecycle / ingestion -------------------------------------------------
    def ingest(self, record: Dict[str, Any]) -> None:
        """Ingest a single Semantiva trace record."""

        record_type = record.get("record_type")
        if record_type == "run_space_start":
            self._ingest_run_space_start(record)
        elif record_type == "run_space_end":
            self._ingest_run_space_end(record)
        elif record_type == "pipeline_start":
            self._ingest_pipeline_start(record)
        elif record_type == "pipeline_end":
            self._ingest_pipeline_end(record)
        elif record_type == "ser":
            self._ingest_ser(record)
        else:
            # tolerate unknown records for forward compatibility
            return

    def ingest_many(self, records: Iterable[Dict[str, Any]]) -> None:
        for record in records:
            self.ingest(record)

    # ---- query helpers ---------------------------------------------------------
    def get_run(self, run_id: str) -> Optional[RunAggregate]:
        return self._runs.get(run_id)

    def iter_runs(self) -> Iterable[RunAggregate]:
        return self._runs.values()

    def get_launch(self, launch_id: str, attempt: int) -> Optional[LaunchAggregate]:
        attempt_int = _coerce_int(attempt)
        if attempt_int is None:
            return None
        return self._launches.get((launch_id, attempt_int))

    def iter_launches(self) -> Iterable[LaunchAggregate]:
        return self._launches.values()

    # ---- completeness ----------------------------------------------------------
    def finalize_run(self, run_id: str) -> RunCompleteness:
        run = self._runs.get(run_id)
        if not run:
            return RunCompleteness(
                run_id=run_id,
                status=cast(Literal["complete", "partial", "invalid"], "invalid"),
                problems=["unknown_run"],
                missing_nodes=[],
                orphan_nodes=[],
                nonterminal_nodes=[],
                summary={},
            )

        expected_nodes = _expected_nodes(run.pipeline_spec_canonical)
        observed_nodes = set(run.nodes.keys())

        problems: List[str] = []
        if not run.saw_start:
            problems.append("missing_pipeline_start")
        if not run.saw_end:
            problems.append("missing_pipeline_end")
        if run.start_ts and run.end_ts and run.start_ts > run.end_ts:
            problems.append("start_ts_gt_end_ts")

        missing = sorted(expected_nodes - observed_nodes) if expected_nodes else []
        orphan = sorted(observed_nodes - expected_nodes) if expected_nodes else []
        nonterminal = sorted(
            [
                node_id
                for node_id, node in run.nodes.items()
                if node.last_status not in _TERMINAL
            ]
        )

        if run.saw_start and run.saw_end:
            status_val: Literal["complete", "partial", "invalid"] = "complete"
        elif not run.saw_start and not run.saw_end and observed_nodes:
            status_val = "invalid"
        elif run.saw_start or run.saw_end or observed_nodes:
            status_val = "partial"
        else:
            status_val = "invalid"

        coverage = None
        if expected_nodes:
            coverage = round(
                len(observed_nodes & expected_nodes)
                / max(len(expected_nodes), 1)
                * 100,
                2,
            )

        summary = {
            "nodes_total_expected": len(expected_nodes) if expected_nodes else None,
            "nodes_observed": len(observed_nodes),
            "coverage_pct": coverage,
            "has_start": run.saw_start,
            "has_end": run.saw_end,
        }

        return RunCompleteness(
            run_id=run.run_id,
            status=status_val,
            problems=problems,
            missing_nodes=missing,
            orphan_nodes=orphan,
            nonterminal_nodes=nonterminal,
            summary=summary,
        )

    def finalize_launch(self, launch_id: str, attempt: int) -> LaunchCompleteness:
        attempt_int = _coerce_int(attempt)
        if attempt_int is None:
            return LaunchCompleteness(
                run_space_launch_id=launch_id,
                run_space_attempt=0,
                status=cast(Literal["complete", "partial", "invalid"], "invalid"),
                problems=["unknown_launch"],
                summary={"requested_attempt": attempt},
            )

        key = (launch_id, attempt_int)
        launch = self._launches.get(key)
        if not launch:
            return LaunchCompleteness(
                run_space_launch_id=launch_id,
                run_space_attempt=attempt_int,
                status=cast(Literal["complete", "partial", "invalid"], "invalid"),
                problems=["unknown_launch"],
                summary={},
            )

        problems: List[str] = []
        if not launch.saw_start:
            problems.append("missing_run_space_start")
        if not launch.saw_end:
            problems.append("missing_run_space_end")

        run_status_counts = {"complete": 0, "partial": 0, "invalid": 0}
        for run_id in launch.pipelines:
            completeness = self.finalize_run(run_id)
            run_status_counts[completeness.status] += 1

        status_val: Literal["complete", "partial", "invalid"]
        if not launch.saw_start and launch.pipelines:
            status_val = "invalid"
        elif launch.saw_start and launch.saw_end:
            if run_status_counts["partial"] or run_status_counts["invalid"]:
                status_val = "partial"
            else:
                status_val = "complete"
        elif launch.saw_start or launch.saw_end or launch.pipelines:
            status_val = "partial"
        else:
            status_val = "invalid"

        summary = {
            "runs_total": len(launch.pipelines),
            "runs_by_status": run_status_counts,
            "planned_run_count": launch.planned_run_count,
        }
        return LaunchCompleteness(
            run_space_launch_id=launch.run_space_launch_id,
            run_space_attempt=launch.run_space_attempt,
            status=status_val,
            problems=problems,
            summary=summary,
        )

    def finalize_all(self) -> Tuple[List[RunCompleteness], List[LaunchCompleteness]]:
        run_results = [self.finalize_run(run.run_id) for run in self._runs.values()]
        launch_results = [
            self.finalize_launch(launch_id, attempt)
            for launch_id, attempt in self._launches.keys()
        ]
        return run_results, launch_results

    # ---- private helpers -------------------------------------------------------
    def _ingest_run_space_start(self, record: Dict[str, Any]) -> None:
        launch_id = record.get("run_space_launch_id")
        attempt = _coerce_int(record.get("run_space_attempt"))
        if not launch_id or attempt is None:
            return
        key = (launch_id, attempt)
        launch = self._launches.get(key)
        if not launch:
            launch = LaunchAggregate(
                run_space_launch_id=launch_id, run_space_attempt=attempt
            )
            self._launches[key] = launch
        launch.saw_start = True
        if record.get("run_space_spec_id") is not None:
            launch.run_space_spec_id = record.get("run_space_spec_id")
        if record.get("run_space_inputs_id") is not None:
            launch.run_space_inputs_id = record.get("run_space_inputs_id")
        if record.get("run_space_planned_run_count") is not None:
            launch.planned_run_count = record.get("run_space_planned_run_count")
        if record.get("run_space_input_fingerprints") is not None:
            launch.input_fingerprints = record.get("run_space_input_fingerprints")

    def _ingest_run_space_end(self, record: Dict[str, Any]) -> None:
        launch_id = record.get("run_space_launch_id")
        attempt = _coerce_int(record.get("run_space_attempt"))
        if not launch_id or attempt is None:
            return
        key = (launch_id, attempt)
        launch = self._launches.get(key)
        if not launch:
            launch = LaunchAggregate(
                run_space_launch_id=launch_id, run_space_attempt=attempt
            )
            self._launches[key] = launch
        launch.saw_end = True

    def _ingest_pipeline_start(self, record: Dict[str, Any]) -> None:
        run_id = record.get("run_id")
        if not run_id:
            return
        run = self._runs.get(run_id)
        if not run:
            run = RunAggregate(run_id=run_id)
            self._runs[run_id] = run
        run.saw_start = True
        if record.get("pipeline_id") is not None:
            run.pipeline_id = record.get("pipeline_id")
        if record.get("pipeline_spec_canonical") is not None:
            run.pipeline_spec_canonical = record.get("pipeline_spec_canonical")
        ts = record.get("ts") or (record.get("timing") or {}).get("started_at")
        if ts and (run.start_ts is None or ts < run.start_ts):
            run.start_ts = ts

        launch_id = record.get("run_space_launch_id")
        attempt = _coerce_int(record.get("run_space_attempt"))
        if launch_id is not None:
            run.run_space_launch_id = launch_id
        if attempt is not None:
            run.run_space_attempt = attempt
        if launch_id is not None and attempt is not None:
            key = (launch_id, attempt)
            launch = self._launches.get(key)
            if not launch:
                launch = LaunchAggregate(
                    run_space_launch_id=launch_id, run_space_attempt=attempt
                )
                self._launches[key] = launch
            launch.pipelines.add(run_id)

    def _ingest_pipeline_end(self, record: Dict[str, Any]) -> None:
        run_id = record.get("run_id")
        if not run_id:
            return
        run = self._runs.get(run_id)
        if not run:
            run = RunAggregate(run_id=run_id)
            self._runs[run_id] = run
        run.saw_end = True
        ts = record.get("ts") or (record.get("timing") or {}).get("finished_at")
        if ts and (run.end_ts is None or ts > run.end_ts):
            run.end_ts = ts

    def _ingest_ser(self, record: Dict[str, Any]) -> None:
        identity = record.get("identity") or {}
        run_id = identity.get("run_id")
        node_id = identity.get("node_id")
        if not run_id or not node_id:
            return
        run = self._runs.get(run_id)
        if not run:
            run = RunAggregate(run_id=run_id)
            self._runs[run_id] = run
        node = run.nodes.get(node_id)
        if not node:
            node = NodeAggregate(node_id=node_id)
            run.nodes[node_id] = node

        ts = record.get("ts") or (record.get("timing") or {}).get("started_at")
        if ts:
            if node.first_ts is None or ts < node.first_ts:
                node.first_ts = ts
            if node.last_ts is None or ts > node.last_ts:
                node.last_ts = ts
        seq = record.get("seq")
        if isinstance(seq, int):
            node.last_seq = seq
        status = record.get("status") or "unknown"
        node.counts[status] = node.counts.get(status, 0) + 1
        node.last_status = status
        node.timing = record.get("timing") or {}
        node.last_error = record.get("error") if status == "error" else None


def _expected_nodes(spec: Optional[Dict[str, Any]]) -> Optional[set[str]]:
    if not spec:
        return None
    nodes = spec.get("nodes")
    if not isinstance(nodes, list):
        return None
    collected: set[str] = set()
    for entry in nodes:
        if isinstance(entry, dict):
            node_uuid = entry.get("node_uuid")
            if node_uuid is not None:
                collected.add(cast(str, node_uuid))
    return collected or None


def _coerce_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
