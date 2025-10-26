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

"""Comprehensive tests for SER preconditions and postconditions checks.

This test module validates that all check structures in SER records conform to
the v1 schema field naming conventions and that all checks are properly validated.
"""

import json
from pathlib import Path

import pytest

from semantiva.configurations import load_pipeline_from_yaml
from semantiva.context_processors import ContextType
from semantiva.data_types import NoDataType
from semantiva.pipeline import Pipeline, Payload
from semantiva.trace.drivers.jsonl import JsonlTraceDriver


def test_required_keys_present_check_structure(tmp_path: Path) -> None:
    """Test that required_keys_present check uses correct field names."""
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
    - processor: "FloatAddOperation"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)

    # Run with missing required key to trigger FAIL
    with pytest.raises(KeyError):
        pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    add_ser = next(
        r
        for r in records
        if r.get("record_type") == "ser"
        and r.get("processor", {}).get("ref", "").endswith("FloatAddOperation")
    )

    pre_checks = {
        entry["code"]: entry for entry in add_ser["assertions"]["preconditions"]
    }
    assert "required_keys_present" in pre_checks

    check = pre_checks["required_keys_present"]
    assert check["result"] == "FAIL"
    assert "details" in check

    # Verify v1 schema field names
    details = check["details"]
    assert "expected_keys" in details, "Should use 'expected_keys' not 'expected'"
    assert "missing_keys" in details, "Should use 'missing_keys' not 'missing'"
    assert isinstance(details["expected_keys"], list)
    assert isinstance(details["missing_keys"], list)
    assert "addend" in details["expected_keys"]
    assert "addend" in details["missing_keys"]


def test_required_keys_present_pass(tmp_path: Path) -> None:
    """Test required_keys_present check when all keys are present."""
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
    - processor: "FloatAddOperation"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)

    # Provide required key
    payload = Payload(NoDataType(), ContextType({"addend": 5.0}))
    pipeline.process(payload)
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    add_ser = next(
        r
        for r in records
        if r.get("record_type") == "ser"
        and r.get("status") == "succeeded"
        and r.get("processor", {}).get("ref", "").endswith("FloatAddOperation")
    )

    pre_checks = {
        entry["code"]: entry for entry in add_ser["assertions"]["preconditions"]
    }
    check = pre_checks["required_keys_present"]
    assert check["result"] == "PASS"

    details = check["details"]
    assert "expected_keys" in details
    assert "missing_keys" in details
    assert details["missing_keys"] == []


def test_input_type_ok_check_structure(tmp_path: Path) -> None:
    """Test that input_type_ok check is present and well-formed."""
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    ser = next(r for r in records if r.get("record_type") == "ser")

    pre_checks = {entry["code"]: entry for entry in ser["assertions"]["preconditions"]}
    assert "input_type_ok" in pre_checks

    check = pre_checks["input_type_ok"]
    assert "result" in check
    assert check["result"] in ["PASS", "FAIL", "WARN"]
    assert "details" in check
    assert "expected" in check["details"]
    assert "actual" in check["details"]


def test_output_type_ok_check_structure(tmp_path: Path) -> None:
    """Test that output_type_ok check is present and well-formed."""
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    ser = next(r for r in records if r.get("record_type") == "ser")

    post_checks = {
        entry["code"]: entry for entry in ser["assertions"]["postconditions"]
    }
    assert "output_type_ok" in post_checks

    check = post_checks["output_type_ok"]
    assert "result" in check
    assert check["result"] in ["PASS", "FAIL", "WARN"]
    assert "details" in check
    assert "expected" in check["details"]
    assert "actual" in check["details"]


def test_context_writes_realized_check_structure(tmp_path: Path) -> None:
    """Test that context_writes_realized check uses correct v1 field names."""
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
    - processor: "FloatBasicProbe"
      context_key: "ser_checks.probe"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    probe_ser = next(
        r
        for r in records
        if r.get("record_type") == "ser"
        and r.get("processor", {}).get("ref", "").endswith("FloatBasicProbe")
    )

    post_checks = {
        entry["code"]: entry for entry in probe_ser["assertions"]["postconditions"]
    }
    assert "context_writes_realized" in post_checks

    check = post_checks["context_writes_realized"]
    assert "result" in check
    assert "details" in check

    # Verify v1 schema field names
    details = check["details"]
    assert "created_keys" in details, "Should use 'created_keys' not 'created'"
    assert "updated_keys" in details, "Should use 'updated_keys' not 'updated'"
    assert "missing_keys" in details, "Should use 'missing_keys' not 'missing'"

    assert isinstance(details["created_keys"], list)
    assert isinstance(details["updated_keys"], list)
    assert isinstance(details["missing_keys"], list)

    # Check should pass (missing_keys should be empty)
    assert details["missing_keys"] == []
    assert check["result"] == "PASS"


def test_context_writes_realized_fail_on_missing(tmp_path: Path) -> None:
    """Test context_writes_realized correctly identifies missing context writes."""
    # This test requires a processor that declares it will create keys but doesn't
    # For now, we just verify the structure exists even when PASS
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    ser = next(r for r in records if r.get("record_type") == "ser")

    post_checks = {
        entry["code"]: entry for entry in ser["assertions"]["postconditions"]
    }
    check = post_checks["context_writes_realized"]

    # Even when no writes, structure should exist
    assert "created_keys" in check["details"]
    assert "updated_keys" in check["details"]
    assert "missing_keys" in check["details"]


def test_config_valid_check_structure(tmp_path: Path) -> None:
    """Test that config_valid check structure when present.

    Note: Invalid parameters now raise an exception before pipeline execution,
    so we just verify the check structure exists in valid cases.
    """
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    ser = next(r for r in records if r.get("record_type") == "ser")

    pre_checks = {entry["code"]: entry for entry in ser["assertions"]["preconditions"]}

    # config_valid check may or may not be present depending on validation
    # If present, it should have proper structure
    if "config_valid" in pre_checks:
        check = pre_checks["config_valid"]
        assert "result" in check
        assert check["result"] in ["PASS", "FAIL", "WARN"]
        assert "details" in check
        assert "invalid" in check["details"]


def test_all_checks_have_required_fields(tmp_path: Path) -> None:
    """Test that all checks conform to the schema's check definition."""
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
    - processor: "FloatBasicProbe"
      context_key: "ser_checks.probe"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)
    pipeline.process()
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    ser_records = [r for r in records if r.get("record_type") == "ser"]

    for ser in ser_records:
        # Check all preconditions
        for check in ser["assertions"]["preconditions"]:
            assert "code" in check, f"Check missing 'code': {check}"
            assert "result" in check, f"Check missing 'result': {check}"
            assert check["result"] in [
                "PASS",
                "FAIL",
                "WARN",
            ], f"Invalid result: {check['result']}"
            # details is optional but if present should be object or null
            if "details" in check:
                assert isinstance(check["details"], (dict, type(None)))

        # Check all postconditions
        for check in ser["assertions"]["postconditions"]:
            assert "code" in check, f"Check missing 'code': {check}"
            assert "result" in check, f"Check missing 'result': {check}"
            assert check["result"] in [
                "PASS",
                "FAIL",
                "WARN",
            ], f"Invalid result: {check['result']}"
            if "details" in check:
                assert isinstance(check["details"], (dict, type(None)))


def test_check_field_names_match_context_delta_convention(tmp_path: Path) -> None:
    """Test that check detail fields use same naming convention as context_delta.

    The context_delta uses field names like 'created_keys', 'updated_keys', etc.
    Check details should follow the same convention for consistency.
    """
    cfg = tmp_path / "test.yaml"
    cfg.write_text(
        """
extensions: ["semantiva-examples"]
pipeline:
  nodes:
    - processor: "FloatValueDataSourceWithDefault"
    - processor: "FloatBasicProbe"
      context_key: "ser_checks.probe"
    - processor: "FloatAddOperation"
"""
    )
    nodes = load_pipeline_from_yaml(str(cfg))
    trace_path = tmp_path / "trace.jsonl"
    tracer = JsonlTraceDriver(str(trace_path))
    pipeline = Pipeline(nodes, trace=tracer)

    # Provide addend to avoid error
    payload = Payload(NoDataType(), ContextType({"addend": 2.0}))
    pipeline.process(payload)
    tracer.close()

    records = [json.loads(line) for line in trace_path.read_text().splitlines() if line]
    ser_records = [r for r in records if r.get("record_type") == "ser"]

    for ser in ser_records:
        # Verify context_delta uses _keys suffix
        delta = ser["context_delta"]
        assert "read_keys" in delta
        assert "created_keys" in delta
        assert "updated_keys" in delta
        assert "key_summaries" in delta

        # Verify checks use _keys suffix for key lists
        for check in ser["assertions"]["preconditions"]:
            if check["code"] == "required_keys_present":
                details = check["details"]
                assert "expected_keys" in details, "Should use 'expected_keys'"
                assert "missing_keys" in details, "Should use 'missing_keys'"
                # Old names should NOT exist
                assert "expected" not in details or details.get("expected") is None
                assert "missing" not in details or details.get("missing") is None

        for check in ser["assertions"]["postconditions"]:
            if check["code"] == "context_writes_realized":
                details = check["details"]
                assert "created_keys" in details, "Should use 'created_keys'"
                assert "updated_keys" in details, "Should use 'updated_keys'"
                assert "missing_keys" in details, "Should use 'missing_keys'"
                # Old names should NOT exist
                assert "created" not in details or details.get("created") is None
                assert "updated" not in details or details.get("updated") is None
                assert "missing" not in details or details.get("missing") is None
