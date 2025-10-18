.. _trace_stream_v1:

Trace Stream v1
===============

Semantiva emits a JSON Lines (JSONL) stream with one JSON object per line.
Each line is a **trace record** of a specific type, e.g.:

- ``pipeline_start`` — lifecycle record emitted at the beginning of a run
- ``ser`` — Semantic Execution Record for a completed node
- ``pipeline_end`` — lifecycle record emitted at the end of a run

Validation model
----------------
Validation is **flat** and **compositional**:

1. **Header check** — each record contains a minimal common header:
   ``record_type``, ``schema_version``, ``run_id``.
2. **Type dispatch** — based on ``record_type``, validate the record with the
   corresponding schema.

Each type has its own schema; adding a new type simply means adding a new schema and a registry entry.

Schemas
-------
Common header (required for all records)
   :file:`semantiva/trace/schema/trace_header_v1.schema.json`

Pipeline start event record
   :file:`semantiva/trace/schema/pipeline_start_event_v1.schema.json`

Semantic Execution Record (SER v1)
   :file:`semantiva/trace/schema/semantic_execution_record_v1.schema.json`

Pipeline end event record
   :file:`semantiva/trace/schema/pipeline_end_event_v1.schema.json`

Type registry
-------------
The registry maps ``record_type`` to schema:

:file:`semantiva/trace/schema/trace_registry_v1.json`

This allows validators to load the correct schema per line without a monolithic
umbrella definition.

Example flow (pseudo)
---------------------

.. code-block:: python

   obj = json.loads(line)
   validate(obj, load("trace_header_v1.schema.json"))
   schema_url = registry["records"][obj["record_type"]]
   validate(obj, load(schema_url))

Compatibility
-------------
- ``trace_header_v1`` is intentionally minimal and matches current outputs:
  it requires only ``record_type``, ``schema_version``, and ``run_id``.
- Future optional fields such as ``ts`` and ``seq`` may be emitted and are
  already allowed by the header schema.
- Lifecycle schemas are intentionally permissive (``additionalProperties: true``)
  to accommodate additive fields without schema churn. The type contract is
  enforced via the ``record_type`` constant and required header fields.

See also
--------
- :doc:`schema_semantic_execution_record_v1`
- :doc:`glossary`
