Architects & system designers
=============================

This page is for people who **design systems around Semantiva**:

- You care about how Semantiva fits into a larger architecture: orchestration,
  storage, observability, lineage.
- You want a clear picture of **execution, inspection and trace flows**,
  not just individual pipelines or components.
- You may own **standards and conventions** around pipelines, SER, run spaces
  and contracts for your organisation.

If you mainly run and tweak existing pipelines, see
:doc:`pipeline_users` instead.

If you primarily write components without owning wider system design, see
:doc:`framework_developers`.

.. admonition:: New to Semantiva?

   If you have never run a Semantiva pipeline before, **start with**
   :doc:`../getting_started`, then follow :doc:`pipeline_users` and
   :doc:`framework_developers`.

   Come back to this page once you are comfortable with pipelines, components
   and basic inspection.

------------------------------
What you should know already
------------------------------

Before you use this page as your main guide, you should:

- Have followed :doc:`../getting_started`, :doc:`pipeline_users` and
  :doc:`framework_developers`.
- Be comfortable with:

  - Reading and reviewing pipeline YAMLs for non-trivial workloads.
  - Understanding the responsibilities of DataOperation, DataProbe and
    ContextProcessor components.
  - Running ``pytest`` and ``semantiva dev lint`` as part of a development
    workflow.

- Have a rough picture that:

  - Semantiva executes **graphs** of nodes (pipelines) over payloads with
    **data and context**.
  - Execution is recorded as **Semantic Execution Records (SER)** and related
    trace artefacts.
  - Contracts and SVA rules (including ``SVA250`` and friends) encode
    architectural invariants in a machine-checkable way.

If any of that is unfamiliar, revisit :doc:`pipeline_users`,
:doc:`framework_developers` and :doc:`../concepts` first.

------------------------------
Your learning path (301+)
------------------------------

Once you are comfortable as a pipeline user and component author, this is the
recommended path for **architects and system designers**.

Step 1 - Get the high-level execution & trace picture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start with the **inspection and trace** side of the system:

- :doc:`../inspection` — why Semantiva records execution the way it does; how
  SER, traces and run spaces fit together.
- :doc:`../ser` — high-level overview of the Semantic Execution Record:
  what each SER describes, and how it relates to a node run.
- :doc:`../run_space` — how executions are grouped into run spaces
  (experiments, campaigns, workflows).

At this stage, you should focus on:

- How **node-level execution** becomes **SER JSONL files**.
- How run spaces organise multiple runs and variations.
- Where, in your architecture, SER and run spaces would be stored and
  consumed (file systems, object stores, trace viewers, etc.).

Step 2 - Understand the core architecture slices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, read the core architecture docs with an “integration” mindset:

- :doc:`../architecture/pipeline_schema` — how pipelines are represented as
  graphs; which parts are user-facing vs internal.
- :doc:`../architecture/context_processing` — how context processing,
  observers and validators are wired (important for understanding invariants
  like those enforced by ``SVA250``).
- :doc:`../architecture/registry` — where processors and other components
  come from, and how they are discovered.

As an architect, you should be able to answer:

- Which artefacts are **static configuration** (pipeline schema, registry
  entries) vs **runtime** (SER, traces, run spaces).
- Where extension points are: new processors, new transports, custom registries.
- How Semantiva's own invariants (as documented in contracts and architecture)
  align with your organisation's design principles.

Configuration artefacts
-----------------------

In most organisations, **YAML pipeline configurations** are the governed
configuration artefact for Semantiva:

- YAML pipelines are versioned, validated (via :doc:`../contracts` and
  :command:`semantiva dev lint`) and promoted across environments.
- YAML is the source for building execution graphs in production
  (see :doc:`../pipelines_yaml` and :doc:`../architecture/pipeline_schema`).

Semantiva also exposes a Python API for constructing pipelines
(:doc:`../pipelines_python`), which is extremely useful for internal
testing, simulation and R&D workflows. These Python pipelines should
be treated as **internal tooling**, not as the system-of-record
configuration.

Step 3 - Tie SER, trace streams and aggregation together
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you have the basic slices, go deeper into the trace pipeline:

- :doc:`../schema_semantic_execution_record_v1` — reference for SER v1 schema.
- :doc:`../trace_stream_v1` — how SERs are turned into trace streams.
- :doc:`../trace_aggregator_v1` — how traces are aggregated into higher-level
  structures.
- :doc:`../trace_graph_alignment` — how traces map back to pipeline graphs.

You do not need to memorise every field, but you should understand:

- How a **single node run** flows into SER → trace stream → aggregated view.
- Which artefacts external tools (e.g. Semantiva Studio Viewer) consume.
- What guarantees you get about **identity and provenance** across these
  stages.

Step 4 - Look at contracts as architecture spec
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contracts and SVA rules act as a **compact architecture specification**:

- :doc:`../contracts` — how contracts are defined and enforced; how
  ``semantiva dev lint`` operationalises them.
- The embedded catalog (``contracts_catalog``) — the list of rules, including:

  - Rules around data and context typing.
  - Context key metadata (created/suppressed/injected keys).
  - Signature invariants such as ``SVA250`` (no ``ContextType`` in
    ``_process_logic``).

As an architect you should:

- Treat these rules as part of the **system's architecture**, not just
  implementation details.
- Use them to derive **organisational conventions** (e.g. how components
  are allowed to see and modify context, how identity is attached to nodes).

Step 5 - Connect Semantiva to your wider system
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, map Semantiva onto your environment:

- :doc:`../execution` — overview of orchestrators, executors and transports:
  where execution lives and how it can be embedded or driven externally.
- :doc:`../run_space_lifecycle` and :doc:`../run_space_emission` — how runs
  are created, updated and closed, and how SER is emitted.
- :doc:`../studio_viewer` — how Semantiva Studio Viewer consumes run and trace
  artefacts to provide interactive exploration.
- :doc:`../development/testing_strategies` — how Semantiva components and
  pipelines fit into CI and system-level testing.

At this point you should be able to sketch:

- Where Semantiva sits relative to schedulers, workflow engines, data stores
  and observability tools.
- Which boundaries you need to protect (e.g. what is allowed to mutate
  context; where identity is assigned and propagated).
- How you would onboard new teams into Semantiva across the three personas
  (pipeline users, component authors, architects).

---------------------------------------
Architecture overview for integrators
---------------------------------------

This section summarises the Semantiva architecture from an integration point of
view. Use it as a mental map while you read the detailed docs.

Execution core
~~~~~~~~~~~~~~

- **Pipelines** are declared as graphs (see :doc:`../architecture/pipeline_schema`):

  - Nodes wrap processors (DataOperation, DataProbe, ContextProcessor).
  - Edges describe data flow and dependencies.
  - Pipelines are static artefacts, typically versioned alongside code.

- **Execution** operates on a **Payload**:

  - ``Payload.data`` carries domain data.
  - ``Payload.context`` carries metadata and state.
  - Nodes never receive the context object directly in their processors'
    business logic; context is mediated via observers and contracts.

Inspection & trace stack
~~~~~~~~~~~~~~~~~~~~~~~~

- For every node run, Semantiva emits a **Semantic Execution Record (SER)**:

  - Contains identity (run, pipeline, node).
  - Records parameter sources, context deltas, data summaries, timing and
    status.
  - Stored as JSONL (one SER per line).

- SERs are then:

  - Turned into **trace streams** (for streaming analysis).
  - Aggregated by the **trace aggregator** into higher-level artefacts
    (e.g. run graphs, summaries).
  - Consumed by tools like **Semantiva Studio Viewer** to support exploration,
    debugging and reporting.

Contracts & invariants
~~~~~~~~~~~~~~~~~~~~~~

- Semantiva's **contracts** (SVA rules) express **architectural invariants**
  such as:

  - How types are declared on processors.
  - How context keys are introduced, suppressed or injected.
  - How processors may (and may not) relate to context.

- These rules are enforced by ``semantiva dev lint`` and should be treated as:

  - A **machine-checkable architecture spec**.
  - A key input when you define internal guidelines for Semantiva usage.

Extension & integration points
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As an architect, you will often look at:

- **Component families** (documented in :doc:`../creating_components` and
  :doc:`../data_operations` / :doc:`../data_probes` / :doc:`../context_processors`)
  as extension points for domain logic.
- **Registry** (:doc:`../architecture/registry`) as the way to manage and
  expose these components.
- **Execution & transports** (:doc:`../execution`) as integration points for:

  - External schedulers / workflow engines.
  - Custom storage for SER and run spaces.
  - Organisation-specific tooling around traces and reports.

----------------------------------------------
Common tasks and where to look in the docs
----------------------------------------------

This section is a quick **router** for common architectural tasks and where to
start in the documentation.

Evaluate whether Semantiva fits a system design
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** decide how Semantiva would integrate into an existing or
  proposed architecture.
- **Look at:**

  - :doc:`../inspection` and :doc:`../ser` (what execution metadata you get).
  - :doc:`../execution` (how execution is organised).
  - :doc:`../run_space` and :doc:`../run_space_lifecycle` (how runs and
    experiments are structured).

Define organisational conventions for pipelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** standardise how teams design and structure pipelines.
- **Look at:**

  - :doc:`../pipeline` and :doc:`../architecture/pipeline_schema` (pipeline
    structure and graph model).
  - :doc:`../contracts` (rules you can rely on as global invariants).
  - :doc:`../glossary` (shared terminology for documentation and reviews).

Integrate SER & traces with observability tooling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** feed Semantiva traces into existing monitoring/logging
  systems or custom dashboards.
- **Look at:**

  - :doc:`../ser` and :doc:`../schema_semantic_execution_record_v1` (data
    model).
  - :doc:`../trace_stream_v1` and :doc:`../trace_aggregator_v1` (aggregation
    and streaming).
  - :doc:`../studio_viewer` (how one consumer visualises SER and trace data).

Design extension points and internal libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** create internal libraries of processors or domain-specific
  building blocks.
- **Look at:**

  - :doc:`../creating_components` and :doc:`framework_developers` (authoring).
  - :doc:`../architecture/registry` (component registration & discovery).
  - :doc:`../contracts` (constraints and guarantees your libraries should
    uphold).

Plan governance, CI and quality gates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **You want to:** define how Semantiva fits into CI/CD and technical
  governance.
- **Look at:**

  - :doc:`../contracts` and :doc:`../development/testing_strategies` (how to
    enforce contracts and write effective tests).
  - :doc:`../cli` (commands to run in CI: lint, inspection, tests).
  - :doc:`../logger` (logging behaviour, if you integrate with central logging).
