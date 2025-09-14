from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_trace_converter(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "pipeline_start",
                        "schema_version": 1,
                        "pipeline_id": "plid-1",
                        "run_id": "run-1",
                        "canonical_spec": {"nodes": [], "edges": []},
                        "meta": {"num_nodes": 1},
                    }
                ),
                json.dumps(
                    {
                        "type": "node",
                        "phase": "after",
                        "address": {
                            "pipeline_run_id": "run-1",
                            "pipeline_id": "plid-1",
                            "node_uuid": "n-1",
                        },
                        "params": {},
                        "input_payload": None,
                        "output_payload": None,
                        "error_type": None,
                        "error_msg": None,
                        "event_time_utc": "2025-01-01T00:00:00Z",
                        "t_wall": 0.1,
                        "t_cpu": 0.05,
                        "out_data_hash": "sha256-abc",
                        "post_context_hash": "sha256-def",
                        "plan_id": None,
                        "plan_epoch": 0,
                    }
                ),
                json.dumps(
                    {
                        "type": "pipeline_end",
                        "schema_version": 1,
                        "run_id": "run-1",
                        "summary": {"status": "ok"},
                    }
                ),
            ]
        )
    )
    cmd = [
        sys.executable,
        "-m",
        "semantiva.semantiva",
        "trace",
        "convert",
        "--from",
        "trace-v1",
        "--to",
        "ser-v1.1",
        str(legacy),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    records = [json.loads(line) for line in res.stdout.splitlines() if line.strip()]
    ser = next(r for r in records if r.get("type") == "ser")
    assert ser["schema_version"] == 2
    assert ser["timing"]["cpu_ms"] == 50
