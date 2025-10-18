import json
import pathlib

import jsonschema
from referencing import Registry, Resource


def _load(path: str):
    return json.loads(pathlib.Path(path).read_text())


TRACE_HEADER = _load("semantiva/trace/schema/trace_header_v1.schema.json")
RUN_SPACE_START = _load("semantiva/trace/schema/run_space_start_event_v1.schema.json")
RUN_SPACE_END = _load("semantiva/trace/schema/run_space_end_event_v1.schema.json")
PIPELINE_START = _load("semantiva/trace/schema/pipeline_start_event_v1.schema.json")

REGISTRY = Registry().with_resources(
    (
        (
            "https://semantiva.tech/schemas/trace/v1/trace_header_v1.schema.json",
            Resource.from_contents(TRACE_HEADER),
        ),
    )
)


def _validate(schema: dict, instance: dict) -> None:
    jsonschema.Draft202012Validator(schema, registry=REGISTRY).validate(instance)


def test_run_space_start_self_contained():
    record = {
        "record_type": "run_space_start",
        "schema_version": 1,
        "run_id": "rs-1",
        "run_space_spec_id": "a" * 64,
        "run_space_launch_id": "launch-uuid",
        "run_space_attempt": 1,
    }

    _validate(RUN_SPACE_START, record)


def test_run_space_start_with_inputs():
    record = {
        "record_type": "run_space_start",
        "schema_version": 1,
        "run_id": "rs-2",
        "run_space_spec_id": "a" * 64,
        "run_space_inputs_id": "b" * 64,
        "run_space_launch_id": "launch-uuid",
        "run_space_attempt": 1,
        "run_space_input_fingerprints": [
            {
                "role": "runs_csv",
                "uri": "file:///runs.csv",
                "digest": {"sha256": "c" * 64},
                "size_bytes": 123,
            }
        ],
    }

    _validate(RUN_SPACE_START, record)


def test_run_space_end_requires_launch_and_attempt():
    record = {
        "record_type": "run_space_end",
        "schema_version": 1,
        "run_id": "rs-3",
        "run_space_launch_id": "launch-uuid",
        "run_space_attempt": 1,
    }

    _validate(RUN_SPACE_END, record)


def test_pipeline_start_linked_to_run_space():
    record = {
        "record_type": "pipeline_start",
        "schema_version": 1,
        "run_id": "p-1",
        "pipeline_id": "pid",
        "pipeline_spec_canonical": {},
        "run_space_spec_id": "a" * 64,
        "run_space_inputs_id": "b" * 64,
        "run_space_launch_id": "launch-uuid",
        "run_space_attempt": 1,
    }

    _validate(PIPELINE_START, record)
