.. _trace_stream_v1:

Trace Stream v1
===============

Semantiva emits a JSON Lines (JSONL) stream with one JSON object per line.
Each line is a **trace record** of a specific type, e.g.:

- ``pipeline_start`` — lifecycle record emitted at the beginning of a run
- ``ser`` — Semantic Execution Record for a completed node
- ``pipeline_end`` — lifecycle record emitted at the end of a run

See also: :ref:`trace_aggregator_v1` for per-run and per-launch aggregation and completeness.

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

Run-Space lifecycle records
   :file:`semantiva/trace/schema/run_space_start_event_v1.schema.json`
   :file:`semantiva/trace/schema/run_space_end_event_v1.schema.json`

Pipeline lifecycle records
   :file:`semantiva/trace/schema/pipeline_start_event_v1.schema.json`
   :file:`semantiva/trace/schema/pipeline_end_event_v1.schema.json`

   The pipeline start record links to an enclosing run-space launch (when present) via a **composite foreign key**:
   
   - ``run_space_launch_id`` + ``run_space_attempt`` — uniquely identifies the launch (retries need both parts)
   
   Run-specific metadata:
   
   - ``run_space_index`` — 0-based position within the launch
   - ``run_space_context`` — parameter values for this specific run
   
   Launch-level constants (``run_space_spec_id``, ``run_space_inputs_id``, ``run_space_combine_mode``, ``run_space_total_runs``) 
   are stored once in the ``run_space_start`` record to eliminate redundancy.

Semantic Execution Record (SER v1)
   :file:`semantiva/trace/schema/semantic_execution_record_v1.schema.json`

Type registry
-------------
The registry maps ``record_type`` to schema:

:file:`semantiva/trace/schema/trace_registry_v1.json`

This allows validators to load the correct schema per line without a monolithic
umbrella definition.

Schema tables
-------------

.. list-table:: Trace Header v1 (shared)
   :header-rows: 1
   :widths: 20 10 20 50

   * - Field
     - Required
     - Type
     - Notes
   * - ``record_type``
     - yes
     - string
     - e.g. ``pipeline_start``, ``run_space_start``, ``ser``
   * - ``schema_version``
     - yes
     - integer (=1)
     - Version pin for the schema family
   * - ``run_id``
     - yes
     - string
     - Per-run identity
   * - ``timestamp``
     - no*
     - RFC3339 string
     - Millisecond precision, UTC ``Z`` suffix
   * - ``seq``
     - no
     - integer ≥0
     - Monotonic sequence number per emitting process

.. note::

   Lifecycle events always emit ``timestamp`` even though the schema keeps it optional for compatibility.

.. list-table:: Pipeline start
   :header-rows: 1
   :widths: 30 10 20 40

   * - Field
     - Required
     - Type
     - Notes
   * - ``pipeline_id``
     - yes
     - string
     - Canonical pipeline identifier
   * - ``pipeline_spec_canonical``
     - yes
     - object
     - Canonicalized pipeline specification
   * - ``run_space_launch_id``
     - no
     - string
     - Foreign key to run_space_start (part 1 of composite FK)
   * - ``run_space_attempt``
     - no
     - integer ≥1
     - Foreign key to run_space_start (part 2 of composite FK, for retry disambiguation)
   * - ``run_space_index``
     - no
     - integer ≥0
     - 0-based position of this run within the launch
   * - ``run_space_context``
     - no
     - object
     - Parameter values for this specific run
   * - ``meta``
     - no
     - object
     - Additional planner/orchestrator metadata

See :doc:`run_space_lifecycle` for lifecycle definitions of the Run-Space identifiers.

.. list-table:: Pipeline end
   :header-rows: 1
   :widths: 20 10 20 50

   * - Field
     - Required
     - Type
     - Notes
   * - ``summary``
     - no
     - object
     - Aggregated counts (implementation-defined keys allowed)

.. list-table:: Run-Space start
   :header-rows: 1
   :widths: 30 10 20 40

   * - Field
     - Required
     - Type
     - Notes
   * - ``run_space_spec_id``
     - yes
     - hex string
     - Plan identity (RSCF v1)
   * - ``run_space_inputs_id``
     - no
     - hex string
     - Inputs snapshot (RSM v1)
   * - ``run_space_launch_id``
     - yes
     - string
     - Launch/session identifier
   * - ``run_space_attempt``
     - yes
     - integer ≥1
     - 1-based retry counter for the launch
   * - ``run_space_combine_mode``
     - yes
     - string
     - Expansion mode: ``combinatorial`` or ``by_position``
   * - ``run_space_total_runs``
     - yes
     - integer ≥0
     - Total number of runs in this launch
   * - ``run_space_max_runs_limit``
     - no
     - integer ≥0
     - Safety limit from configuration (``max_runs``)
   * - ``run_space_planned_run_count``
     - no
     - integer ≥0
     - Planned number of runs
   * - ``run_space_input_fingerprints``
     - no
     - array
     - External input fingerprints with ``uri``/``sha256`` metadata

.. list-table:: Run-Space end
   :header-rows: 1
   :widths: 30 10 20 40

   * - Field
     - Required
     - Type
     - Notes
   * - ``run_space_launch_id``
     - yes
     - string
     - Matches the corresponding start record
   * - ``run_space_attempt``
     - yes
     - integer ≥1
     - Matches the corresponding start record
   * - ``summary``
     - no
     - object
     - Emitted run counts, errors, and additional implementation data

Example flow (pseudo)
---------------------

.. code-block:: python

   obj = json.loads(line)
   validate(obj, load("trace_header_v1.schema.json"))
   schema_url = registry["records"][obj["record_type"]]
   validate(obj, load(schema_url))

Compatibility
-------------
- ``trace_header_v1`` requires ``record_type``, ``schema_version``, and ``run_id``.
  ``timestamp`` and ``seq`` remain optional in the schema for backward compatibility, but the driver
  always emits ``timestamp`` on lifecycle records.
- Lifecycle schemas are intentionally permissive (``additionalProperties: true``)
  to accommodate additive fields without schema churn. The type contract is
  enforced via the ``record_type`` constant and required header fields.

See also
--------
- :doc:`schema_semantic_execution_record_v1`
- :doc:`glossary`
- :doc:`run_space_emission`
