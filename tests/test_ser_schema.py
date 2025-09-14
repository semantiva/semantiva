from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except Exception:  # pragma: no cover - optional dependency
    jsonschema = None
    pytest.skip("jsonschema not installed", allow_module_level=True)

from semantiva.configurations import load_pipeline_from_yaml
from semantiva.pipeline import Pipeline
from semantiva.trace.drivers.jsonl import JSONLTrace


def test_ser_schema_validation(tmp_path: Path) -> None:
    nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
    trace_path = tmp_path / "trace.ser.jsonl"
    tracer = JSONLTrace(str(trace_path))
    Pipeline(nodes, trace=tracer).process()
    tracer.close()
    schema_path = Path("docs/spec/ser_v1_1.schema.json")
    if not schema_path.exists():
        # resolve relative to repository root
        repo_root = Path(__file__).resolve().parents[1]
        alt = repo_root / "docs/spec/ser_v1_1.schema.json"
        if alt.exists():
            schema_path = alt
    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for line in trace_path.read_text().splitlines():
        rec = json.loads(line)
        if rec.get("type") == "ser":
            validator.validate(rec)
