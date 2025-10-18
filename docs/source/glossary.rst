.. _glossary:

Glossary
========

This glossary defines Semantiva’s public concepts as used in the graph model,
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
      Wall/CPU timing of the step; start/finish timestamps and duration in ms.

      **Technical mapping:**
         - SER: ``timing.started_at|finished_at|duration_ms|cpu_ms``

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

Trace & Drivers
---------------

.. glossary::

   Trace
      The append-only sequence of SER entries (and lifecycle events) produced
      during execution.

   JsonlTraceDriver
      A driver that writes each SER as a JSON line to a file (or to a timestamped
      file if given a directory).
