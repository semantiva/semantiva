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
            "timestamp": "2025-01-01T00:00:00.000Z",
            "seq": 1,
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
            "timestamp": "2025-01-01T00:00:01.000Z",
            "seq": 2,
        }
    )
    aggregator.ingest(
        {
            "record_type": "ser",
            "identity": {"run_id": "R1", "pipeline_id": "P1", "node_id": "n1"},
            "status": "succeeded",
            "timing": {
                "wall_ms": 10,
                "started_at": "2025-01-01T00:00:02.000Z",
                "finished_at": "2025-01-01T00:00:03.000Z",
            },
        }
    )
    aggregator.ingest(
        {
            "record_type": "pipeline_end",
            "run_id": "R1",
            "timestamp": "2025-01-01T00:00:04.000Z",
            "seq": 4,
        }
    )
    aggregator.ingest(
        {
            "record_type": "run_space_end",
            "run_space_launch_id": "L1",
            "run_space_attempt": 1,
            "timestamp": "2025-01-01T00:00:05.000Z",
            "seq": 5,
        }
    )

    run_completeness = aggregator.finalize_run("R1")
    assert run_completeness.status == "complete"
    assert run_completeness.summary["coverage_pct"] == 100.0
    # Verify timestamps are captured in the RunAggregate
    run = aggregator.get_run("R1")
    assert run is not None
    assert run.start_timestamp == "2025-01-01T00:00:01.000Z"
    assert run.end_timestamp == "2025-01-01T00:00:04.000Z"

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


def test_timestamp_fallback_from_node_ser():
    """Test that timestamps are synthesized from node SER timing when lifecycle records lack timestamps."""
    aggregator = TraceAggregator()
    # pipeline_start without timestamp
    aggregator.ingest(
        {
            "record_type": "pipeline_start",
            "run_id": "R4",
            "pipeline_id": "P4",
            "pipeline_spec_canonical": {
                "nodes": [{"node_uuid": "n1"}, {"node_uuid": "n2"}]
            },
        }
    )
    # Node SER records with timing - each SER gets a timestamp which becomes first_timestamp/last_timestamp
    aggregator.ingest(
        {
            "record_type": "ser",
            "identity": {"run_id": "R4", "pipeline_id": "P4", "node_id": "n1"},
            "status": "succeeded",
            "timestamp": "2025-01-01T10:00:00.000Z",  # This becomes node.first_timestamp
            "timing": {
                "started_at": "2025-01-01T10:00:00.000Z",
                "finished_at": "2025-01-01T10:00:05.000Z",
            },
        }
    )
    aggregator.ingest(
        {
            "record_type": "ser",
            "identity": {"run_id": "R4", "pipeline_id": "P4", "node_id": "n2"},
            "status": "succeeded",
            "timestamp": "2025-01-01T10:00:10.000Z",  # This becomes node.last_timestamp
            "timing": {
                "started_at": "2025-01-01T10:00:06.000Z",
                "finished_at": "2025-01-01T10:00:10.000Z",
            },
        }
    )
    # pipeline_end without timestamp
    aggregator.ingest({"record_type": "pipeline_end", "run_id": "R4"})

    run_completeness = aggregator.finalize_run("R4")
    assert run_completeness.status == "complete"
    # Verify timestamps were synthesized from node SER timings
    run = aggregator.get_run("R4")
    assert run is not None
    assert run.start_timestamp == "2025-01-01T10:00:00.000Z"  # earliest node timestamp
    assert run.end_timestamp == "2025-01-01T10:00:10.000Z"  # latest node timestamp
