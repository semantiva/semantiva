Concepts
========

Semantiva narrows the gap between bold ideas and concrete code. The framework
promotes **clarity**, **type‑safety**, and **semantic transparency** so that a
pipeline can be read, reasoned about, and audited. The sections below tell the
story behind the core pieces and link to deeper references when you want more
detail.

Domain-Driven & Type-Oriented Design
------------------------------------

Semantiva pipelines are designed around your *domain concepts*. Data types are
not afterthoughts – they are **contracts** between pipeline steps. When you
declare a ``StringLiteralDataType`` or a domain type like ``DNASequence``, you
state the expectations for both data and meaning. These contracts prevent
miswired steps and make intent explicit. For more on defining custom types see
the :doc:`data_types` guide.

Data Types
----------

Data types describe the *shape and semantics* of data moving through a pipeline.
Because every processor declares the types it accepts and returns, mismatched
inputs are caught at configuration time instead of failing deep inside a
workflow. Type-safe workflows communicate purpose: a ``SingleChannelImage``
clearly differs from a ``FloatCollection``. Learn how types enforce these
guarantees in :doc:`data_types`.

Processors
----------

Processors are the workhorses of Semantiva, each with a single
responsibility:

* A **DataOperation** transforms input data.
* A **DataProbe** inspects or logs data without changing it.
* **I/O processors** load or save data from external systems.

Each processor focuses on one task, reinforcing clarity and maintainability.
See :doc:`data_processors` and :doc:`data_io` for implementation details.

Nodes
-----

Pipelines are built from **nodes**, thin wrappers around processors. Nodes are
generated when Semantiva reads your declarative YAML; you rarely subclass them
yourself. They handle the plumbing: feeding data **and** context into processors
and chaining outputs to inputs. The :doc:`pipeline` section shows how nodes fit
into graph execution.

Context Channel
---------------

Alongside domain data flows a mutable **context channel**—a key/value store for
metadata, parameters, or runtime state. Context processors can inspect or
mutate this channel, enabling adaptive behaviours and rich execution traces.
Understanding context manipulation is key to building semantic workflows; dive
deeper in :doc:`context_processors`.

Resolvers & Parameters
----------------------

Declarative specifications in YAML become executable graphs through **resolvers**.
Class resolvers (``slicer:``, ``rename:``, ``delete:``) map concise strings to
Python classes, while parameter resolvers (``model:``) inject runtime objects
without hard‑coding them. This mechanism keeps pipelines declarative yet
flexible. For the full resolver registry and extension mechanism consult
:doc:`registry_and_extensions`.

Dual-Channel Pipeline
---------------------

Every Semantiva pipeline carries two synchronized streams: the **data channel**
and the **context channel**. Data holds your domain objects; context carries the
metadata explaining *how* and *why* each step executes. This dual-channel design
embodies the Epistemic Computing Paradigm (ECP) where computation produces both
results and rationale.

Minimal Epistemic Unit (MEU)
----------------------------

Each execution step yields more than an output. It produces a claim about what
happened, a justification grounded in types and context, and a trace that can be
audited later. This **Minimal Epistemic Unit** allows humans and machines to
reason about a pipeline's behaviour. For a glimpse of how traces capture these
records see :doc:`tracing`.

