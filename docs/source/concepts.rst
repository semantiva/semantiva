Basic Concepts
==============

Semantiva narrows the gap between ideas and executable pipelines. It is built
around **typed payloads**, a **dual data/context channel**, and clear contracts
for every processor.

The payload: data + context
---------------------------

Every Semantiva pipeline step processes a *payload* with two channels:

- **Data channel** - your domain objects (images, arrays, records, models…).
- **Context channel** - structured metadata that flows with the data through
  the pipeline. It carries configuration parameters, derived values, quality
  indicators, and other state used by processors to share information and
  adapt execution.

The two channels always move together. A run is fully described by:

- The pipeline definition and configuration.
- The run-space plan (if any).
- The sequence of payloads (data + context) as they pass through nodes.

Identifiers such as run IDs are assigned by the execution and tracing layers
and are not stored in the context channel.

Data channel: types, operations and collections
-----------------------------------------------

Key concepts on the data side:

- **Data types** - subclasses of the core ``BaseDataType`` class.
  They encode contracts for shape, units and semantics (for example a
  ``SingleChannelImage`` vs. a ``FloatCollection``).
- **Data sources** - components that *produce* data from outside the pipeline.
  They are not processors themselves; factories wrap them so they can participate
  in pipelines as payload processors.
- **Data operations** - processors that transform one data type into another,
  with clear input/output type contracts.
- **Data probes** - processors that observe the data channel and write
  summaries into the context channel.
- **Data sinks** - components that write data out of the pipeline (files, sockets,
  viewers, message buses…). Like sources, they are wrapped by factories and are not
  native processors.

Collections:

- **Data collections** model sequences of data objects of the same base type.
- Modifiers such as ``slice`` and **parameter sweeps** build on top of
  collections to describe families of runs without hand-writing loops.

Context channel
---------------

The context channel is handled by context processors. They:

- Propose context updates and deletions via notifier helpers,
  without direct access to the underlying context object.
- Derive new parameters from existing context and configuration.
- Maintain state across nodes (for example running statistics).
- Record metrics and metadata used by downstream analysis.

Run-space expansion injects values into the initial context for each run. At
runtime there is no distinction between parameters provided by the run-space
and parameters set by other means; all are resolved from the context channel.

Parameter resolution
--------------------

Processor parameters are resolved just before a node runs. Semantiva combines
values from three sources into a single parameter set:

- The node's ``parameters`` mapping from the pipeline configuration.
- Values available in the context channel.
- Defaults declared by the processor's contract.

When multiple sources provide a value for the same parameter, the following
priority applies (from highest to lowest):

1. Explicit values in the node's ``parameters``.
2. Values resolved from the context channel (including run-space injected
   values).
3. Processor-level default values.

This keeps pipeline configuration explicit, while still allowing context and
defaults to supply values when configuration is silent.

Payload operations, pipelines and nodes
---------------------------------------

A pipeline is a directed graph of **nodes**. Each node wraps a processor and has:

- A reference to the processor class or registered name.
- Parameter values (possibly resolved from context or the run-space).
- Ports for incoming and outgoing data.

At runtime:

1. The pipeline expands any pre-processors (such as ``derive`` and sweeps)
   and run-space blocks.
2. Data flows along edges, constrained by data type contracts.
3. Context processors observe and update the context channel.
4. Optional trace drivers observe execution and emit **Semantic Execution
   Records (SER)**.

Processors (data operations, probes, and context processors) and pipeline
nodes operate only on the data and context channels. SER records are produced
by trace drivers attached to the orchestrator and executor and do not change
data or context.

From a user perspective:

- You **define processors** in Python (see :doc:`creating_components`).
- You **configure pipelines** in YAML (see :doc:`pipeline`).
- You **execute** via :doc:`cli` or the Python API, always working with the
  payload abstraction.

For a more visual explanation of how all this fits together:

- :doc:`data_types`
- :doc:`data_processors`
- :doc:`context_processors`
- :doc:`data_collections`

Trace records and trace drivers
-------------------------------

Tracing is an optional layer that records how pipelines execute over time.

- **Semantic Execution Records (SER)** capture which processors ran, how they
  were connected, and summary information about payloads and context at each
  step.
- **Trace drivers** attach to the orchestrator and executor. They observe
  execution events and write SER streams, typically to files or external sinks.

Trace drivers are configured in the pipeline YAML (see
:doc:`architecture/pipeline_schema`) and described in more detail in
:doc:`trace_stream_v1` and :doc:`ser`.