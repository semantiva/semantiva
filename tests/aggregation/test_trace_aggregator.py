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

from semantiva.trace.aggregation.aggregator import TraceAggregator


def test_run_complete_and_launch_complete():
    aggregator = TraceAggregator()
    aggregator.ingest(
        {
            "record_type": "run_space_start",
            "run_space_launch_id": "L1",
            "run_space_attempt": 1,
        }
    )
    aggregator.ingest(
        {
            "record_type": "pipeline_start",
            "run_id": "R1",
            "pipeline_id": "P1",
            "run_space_launch_id": "L1",
            "run_space_attempt": 1,
            "pipeline_spec_canonical": {"nodes": [{"node_uuid": "n1"}]},
        }
    )
    aggregator.ingest(
        {
            "record_type": "ser",
            "identity": {"run_id": "R1", "pipeline_id": "P1", "node_id": "n1"},
            "status": "succeeded",
            "timing": {"wall_ms": 10},
        }
    )
    aggregator.ingest({"record_type": "pipeline_end", "run_id": "R1"})
    aggregator.ingest(
        {
            "record_type": "run_space_end",
            "run_space_launch_id": "L1",
            "run_space_attempt": 1,
        }
    )

    run = aggregator.finalize_run("R1")
    assert run.status == "complete"
    assert run.summary["coverage_pct"] == 100.0

    launch = aggregator.finalize_launch("L1", 1)
    assert launch.status == "complete"
    assert launch.summary["runs_total"] == 1
    assert launch.summary["runs_by_status"]["complete"] == 1


def test_partial_run_without_end_and_orphan_launch():
    aggregator = TraceAggregator()
    aggregator.ingest(
        {"record_type": "pipeline_start", "run_id": "R2", "pipeline_id": "P2"}
    )

    run = aggregator.finalize_run("R2")
    assert run.status == "partial"
    assert "missing_pipeline_end" in run.problems

    launch = aggregator.finalize_launch("Lx", 7)
    assert launch.status == "invalid"
    assert "unknown_launch" in launch.problems


def test_launch_with_partial_run_reports_partial_status():
    aggregator = TraceAggregator()
    aggregator.ingest(
        {
            "record_type": "run_space_start",
            "run_space_launch_id": "L2",
            "run_space_attempt": "2",
        }
    )
    aggregator.ingest(
        {
            "record_type": "pipeline_start",
            "run_id": "R3",
            "pipeline_id": "P3",
            "run_space_launch_id": "L2",
            "run_space_attempt": "2",
        }
    )
    aggregator.ingest(
        {
            "record_type": "run_space_end",
            "run_space_launch_id": "L2",
            "run_space_attempt": 2,
        }
    )

    launch = aggregator.finalize_launch("L2", "2")
    assert launch.status == "partial"
    assert launch.summary["runs_by_status"]["partial"] == 1
