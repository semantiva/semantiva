.. _glossary:

Glossary
========

This glossary defines Semantiva's public concepts as used in the graph model,
runtime execution, and the SER (Semantic Execution Record).

Core Runtime Objects
--------------------

.. glossary::

   Graph (GraphV1)
      The canonical, deterministic representation of a pipeline, including nodes,
      edges, processor references, parameters, and stable identifiers.

      **Ontological role:** Declarative plan that a runtime executes.

      **Technical mapping:**
         - Docs: :doc:`graph`, :doc:`trace_graph_alignment`

      **Usage guidance:** Use *Graph* for the canonical compiled form (not ad-hoc
      YAML or runtime objects).

   Node
      A graph element that binds a :term:`Processor` with parameters and
      participates in edges.

      **Ontological role:** Structural placement of a processor in the graph.

      **Technical mapping:**
         - Graph: each node has a stable identifier (UUID) used in SER
           ``identity.node_id``

      **Usage guidance:** Do not confuse Node (graph element) with Processor
      (class/logic).

   Processor
      A Python class implementing a deterministic operation or an observation.

      **Ontological role:** Executes logic over channels and/or context.

      **Technical mapping:**
         - Graph: ``processor_ref`` (fully-qualified class name)
         - SER: ``processor.ref``, ``processor.parameters``,
           ``processor.parameter_sources``

      **Usage guidance:** *Processor* refers to the class/implementation, not the
      Node.

   Processor Reference
      A fully-qualified class name (FQCN) or descriptor that uniquely identifies a
      Processor class.

      **Ontological role:** Allows reproducible instantiation of processors.

      **Technical mapping:**
         - Graph: ``processor_ref`` (string)
         - SER: ``processor.ref`` (string)

   GraphV1
      Alias for :term:`Graph (GraphV1)` used when referring to the canonical graph
      schema.

   PipelineId
      Deterministic identifier for a pipeline derived from its canonical spec.

      **Technical mapping:** Appears under SER ``identity.pipeline_id`` and graph
      inspection outputs.

   node_uuid
      Stable identifier for a :term:`Node` within the canonical graph.

      **Technical mapping:** Appears as ``identity.node_id`` in SER and in graph
      inspection tables.

   Payload
      Runtime envelope carrying a typed :term:`Data Channel` value plus the active
      :term:`Context Channel` mapping.

      **Ontological role:** Execution payload passed between nodes.

   Resolver
      Mechanism that rewrites configuration fragments (e.g., parameter slicing,
      renaming, template expansion) while building the :term:`Graph (GraphV1)`.

Channels & Data
---------------

.. glossary::

   Data Channel
      The typed data flowing between processors. **Data** is subject to:
      (1) transformation by :term:`Data Operation`, and
      (2) observation by :term:`Data Probe`.

      Observations made by Data Probes are typically **injected into the Context
      Channel** under keys declared in the pipeline configuration.

      **Ontological role:** Carries domain data through the pipeline.

      **Technical mapping:**
         - Summaries may appear under SER ``summaries`` if trace policy enables it.

      **Usage guidance:** Keep Data Channel (data flow) distinct from Context
      Channel (key/value store).

   Context Channel
      A mutable key/value store holding parameters, metadata, and runtime state.

      Context can be modified by :term:`Context Processor` or by
      :term:`Data Processor` that injects key/value entries. Context is observed
      in two independent phases:

      1. **Parameter resolution** — when a processor requires a parameter not
         declared on the node, Semantiva searches the Context Channel to satisfy it.
      2. **SER emission** — optionally, the state of Context **before** and
         **after** node execution and the **mutation delta** are observed and
         recorded.

      **Ontological role:** Shared execution state and metadata plane.

      **Technical mapping:**
         - SER: ``context_delta.read_keys|created_keys|updated_keys|key_summaries``

      **Usage guidance:** Any context-only observation outside SER emission is implemented by a :term:`Context Processor`.

Processor Families
------------------

.. glossary::

   Data Processor
      Any :term:`Processor` that touches the :term:`Data Channel`. Includes
      :term:`Data Operation` and :term:`Data Probe`.

      **Ontological role:** Umbrella term for processors that read from or write
      to the Data Channel.

      **Technical mapping:**
         - Graph: nodes referencing Data Operations or Data Probes
         - SER: ``processor.ref`` reflects the concrete class

   Data Operation
      Transforms values on the :term:`Data Channel` (e.g., filter, normalize, join).

      **Ontological role:** Data transformation.

      **Technical mapping:**
         - Effects may be summarized under SER ``summaries`` depending on trace policy.

   Data Probe
      Observes the :term:`Data Channel` without altering its data output. Probe
      observations are written into the :term:`Context Channel` under declared keys.

      **Ontological role:** Data observation with side-effects in Context.

   Context Processor
      Reads and/or mutates the :term:`Context Channel`. Any observation of context
      outside SER emission must be implemented as a Context Processor.

      **Ontological role:** Context transformation and inspection.

   IO Processor
      Interacts with external systems (read/write). Should capture sufficient
      metadata in Context for provenance (e.g., source path, checksums).

Preprocessing
-------------

.. glossary::

   derive
      Reserved node key; the boundary where **preprocessors** compute or expand
      configuration before execution.

   parameter_sweep
      A preprocessor under :term:`derive` that computes **parameters** from
      **variables** (expressions) and may expand the node into multiple runs.

   parameters (computed)
      The mapping under ``derive.parameter_sweep.parameters``. Keys are **callee
      parameter names**; values are expressions producing call-time values.

   variables
      The mapping under ``derive.parameter_sweep.variables`` defining named
      ranges, explicit sequences, or context-fed sequences.

   required_external_parameters
      Unbound callee argument names still required after preprocessing; displayed
      by inspection so users can fill them via node ``parameters`` or rely on
      callee defaults.

Execution Records (SER Vocabulary)
----------------------------------

.. glossary::

   Semantic Execution Record (SER)
      One JSON record emitted for every completed node execution. Captures
      identity, dependencies, processor details, context delta, assertions, timing,
      status, and optional tags/summaries.

      **Technical mapping:**
         - Schema: :doc:`schema_semantic_execution_record_v1`
         - Driver: JSONL trace driver appends one line per SER

   SERRecord
      In-memory structure passed to drivers that serializes to SER JSON.

   Identity
      Stable identifiers of run, pipeline, and node for the step currently
      recorded.

      **Technical mapping:**
         - SER: ``identity.run_id``, ``identity.pipeline_id``, ``identity.node_id``

   Dependencies
      Upstream node identifiers that provided inputs to this step.

      **Technical mapping:**
         - SER: ``dependencies.upstream``

   Assertions
      Structured check results grouped by phase (preconditions, postconditions,
      invariants), plus environment metadata and redaction policy.

      **Technical mapping:**
         - SER: ``assertions.*`` (including required ``environment``)

   Timing
      Wall/CPU timing of the step; start/finish timestamps and wall-clock duration (ms).

      **Technical mapping:**
         - SER: ``timing.started_at`` | ``timing.finished_at`` | ``timing.wall_ms`` | ``timing.cpu_ms``

   Status
      Final state of the step execution: ``succeeded``, ``error``, ``skipped``,
      ``cancelled``.

   Tags
      Optional labels for correlation and search.

   Summaries
      Optional digests of inputs/outputs/context per trace policy.

   Context Delta
      The context read/write sets and per-key summaries observed at SER emission.

      **Technical mapping:**
         - SER: ``context_delta.*``

Run-Space Identity
------------------

.. glossary::

   RSCF v1
      **Run-Space Configuration Format v1** — Canonical representation of a 
      run-space specification that produces the deterministic ``run_space_spec_id`` 
      identifier.

      **Ontological role:** Plan identity for reproducible run-space launches.

      **Technical mapping:**
         - Identity: ``run_space_spec_id``
         - Docs: :doc:`run_space_lifecycle`, :doc:`run_space_emission`

   RSM v1
      **Run-Space Materialization v1** — Snapshot of external inputs referenced 
      by a run-space plan that produces the deterministic ``run_space_inputs_id`` 
      identifier. Omitted when the run-space is self-contained.

      **Ontological role:** Inputs identity for reproducible run-space launches.

      **Technical mapping:**
         - Identity: ``run_space_inputs_id``
         - Docs: :doc:`run_space_lifecycle`, :doc:`run_space_emission`

Trace & Drivers
---------------

.. glossary::

   Trace
      The append-only sequence of SER entries (and lifecycle events) produced during execution.

   JsonlTraceDriver
      A driver that writes each SER as a JSON line to a file (or to a timestamped file if given a directory).

Run-Space Lifecycle
--------------------

.. glossary::

   by_position
      Index-aligned Run-Space expansion mode. Lists align by index so element *i* travels together.
      See :doc:`run_space` for planner examples.

   combinatorial
      Cartesian Run-Space expansion mode. All combinations across the provided values are materialized.
      See :doc:`run_space` for planner examples.

   Run-Space Spec ID
      ``run_space_spec_id`` — canonical identity of a Run-Space plan (RSCF v1).
      See :doc:`run_space_lifecycle`.

   Run-Space Inputs ID
      ``run_space_inputs_id`` — canonical identity of the external inputs snapshot (RSM v1).
      Emitted when file-based inputs participate in the launch. See :doc:`run_space_lifecycle`.

   Run-Space Launch ID
      ``run_space_launch_id`` — unique launch/session identifier shared by lifecycle, pipeline start, and SER records.
      See :doc:`run_space_lifecycle` and :doc:`trace_stream_v1`.

   Run-Space Attempt
      ``run_space_attempt`` — 1-based retry counter scoped to a launch. Increments on planner-level retries.
      See :doc:`run_space_lifecycle`.

   Planned Run Count
      ``run_space_planned_run_count`` — total number of runs expected from a launch when known.
      Emitted on ``run_space_start`` for inspection and aggregator completeness.

   Planned Run Count (SER)
      ``assertions.args.run_space.total`` — per-run view of the total planned runs exposed in SER metadata.
      See :doc:`schema_semantic_execution_record_v1`.

Aggregation
-----------

.. glossary::

   Core Trace Aggregator
      Service that consumes trace streams and produces Run/Launch aggregates with completeness verdicts.
      See :ref:`trace_aggregator_v1`.

   Run Aggregate
      The in-memory summary of a single pipeline run (keyed by ``run_id``) produced by the Core Trace Aggregator.
      Includes lifecycle presence, node coverage, timing, and a completeness verdict. See :ref:`trace_aggregator_v1`.

   Launch Aggregate
      The in-memory summary of a run-space launch attempt (keyed by ``(run_space_launch_id, run_space_attempt)``).
      Aggregates pipeline runs, links their statuses, and surfaces missing launch lifecycle edges.
      See :ref:`trace_aggregator_v1`.

   Completeness (Trace)
      Deterministic verdict describing whether expected lifecycle edges and node coverage are present for a run or launch.
      See :ref:`trace_aggregator_v1`.

