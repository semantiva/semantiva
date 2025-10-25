.. _schema_semantic_execution_record_v1:

SER v1 JSON Schema
==================

The :term:`Semantic Execution Record (SER)` captures the execution of each :term:`Node`
from a compiled :term:`Graph (GraphV1)` run. This page summarizes the v1 JSON
Schema shipped with Semantiva (``semantiva.trace.schema.semantic_execution_record_v1.schema.json``) and
shows how each field relates to runtime behavior and glossary concepts.

The schema is consumed by the :term:`Trace` pipeline and emitted by the
:term:`JsonlTraceDriver`. For a conceptual mapping between SER entries and the
graph runtime, see :doc:`trace_graph_alignment`.

Loading the Schema
------------------

.. code-block:: python

   from importlib import resources

   schema = resources.files("semantiva.trace.schema") / "semantic_execution_record_v1.schema.json"

Top-Level Structure
-------------------

Each SER JSON object has the following top-level fields:

.. list-table:: Top-level SER fields
   :header-rows: 1

   * - Field
     - Purpose
   * - ``record_type``
     - Constant ``"ser"`` identifying the document type.
   * - ``schema_version``
     - Constant ``1`` indicating the SER major version.
   * - ``identity``
     - Stable identifiers for the run, pipeline, and node being recorded.
   * - ``dependencies``
     - Upstream :term:`Node` identifiers that fed this step.
   * - ``processor``
     - The :term:`Processor` implementation, parameters, and parameter sources.
   * - ``context_delta``
     - Observation of :term:`Context Channel` reads/writes captured at SER emission.
   * - ``assertions``
     - Structured checks with environment metadata and redaction policy.
   * - ``timing``
     - Start/end timestamps plus duration (wall and CPU milliseconds).
   * - ``status``
     - Final state of the step (``succeeded``/``error``/``skipped``/``cancelled``).
   * - ``error`` *(optional)*
     - Structured information about failures when ``status`` is ``error``.
   * - ``tags`` *(optional)*
     - Arbitrary key/value labels for correlation and filtering.
   * - ``summaries`` *(optional)*
     - Digests of inputs/outputs/context depending on trace policy.

Identity & Dependencies
-----------------------

``identity`` contains ``run_id``, ``pipeline_id``, and ``node_id``. These values
correspond to the canonical IDs produced from the :term:`Graph (GraphV1)` and are
used to correlate SER entries with :doc:`graph` inspection outputs.

``dependencies.upstream`` is an array of upstream ``node_id`` values. The runtime
populates this list with the immediate predecessors that satisfied current node
inputs, matching the dependency edges described in :doc:`trace_graph_alignment`.

Processor Block
---------------

The ``processor`` object captures details about the executing :term:`Processor`:

* ``ref`` — fully-qualified class name (:term:`Processor Reference`).
* ``parameters`` — parameter map resolved for this invocation.
* ``parameter_sources`` — origin of each parameter value. Permitted enums are:
  ``"context"`` (drawn from the :term:`Context Channel` during parameter
  resolution), ``"node"`` (declared on the :term:`Node`), and ``"default"``
  (taken from processor defaults).

Because Semantiva separates data and context, processors may fetch values from
both the :term:`Data Channel` and :term:`Context Channel`. The parameter source
metadata documents which channel contributed values, enabling downstream replay
or audits.

Context Delta
-------------

``context_delta`` provides the structured observation of context mutations
during SER emission:

* ``read_keys`` — keys read from the :term:`Context Channel`.
* ``created_keys`` — keys introduced during execution.
* ``updated_keys`` — existing keys whose values changed.
* ``key_summaries`` — per-key digests of changed values (dtype, length, etc.).

This observation occurs during the second context observation phase (SER
emission) described in :term:`Context Channel`. Processors that interact with
context outside of SER emission must do so via a :term:`Context Processor` and
should also update their declared read/write sets so the delta remains accurate.

Assertions
----------

The ``assertions`` object records execution evidence:

* ``preconditions`` and ``postconditions`` — arrays of structured checks that
  demonstrate expectations before and after the processor ran.
* ``invariants`` — additional checks evaluated throughout execution.
* ``environment`` — runtime metadata (Python version, platform, Semantiva build,
  etc.).
* ``redaction_policy`` — declaration of any applied redactions.

Each check item follows the ``check`` definition in the schema, requiring a
``code`` and ``result`` (``PASS``/``WARN``/``FAIL``), with optional ``details``.
This mirrors the evidence captured by the orchestrator described in
:doc:`ser`.

Timing, Status, and Errors
--------------------------

``timing`` captures start/finish instants plus duration metrics:

.. table:: SER timing fields
   :align: left
   :widths: auto

   +--------------+----------+---------+------------------------------------------------------+
   | Field        | Required | Type    | Notes                                                |
   +==============+==========+=========+======================================================+
   | ``started_at`` | yes    | string  | RFC3339 timestamp (UTC ``Z``) for processor start    |
   +--------------+----------+---------+------------------------------------------------------+
   | ``finished_at`` | yes   | string  | RFC3339 timestamp (UTC ``Z``) for processor end      |
   +--------------+----------+---------+------------------------------------------------------+
   | ``wall_ms``  | yes      | integer | Wall-clock duration in milliseconds                  |
   +--------------+----------+---------+------------------------------------------------------+
   | ``cpu_ms``   | no       | integer | CPU time in milliseconds when available              |
   +--------------+----------+---------+------------------------------------------------------+

These values measure the actual runtime of the :term:`Processor` as scheduled
by the orchestrator.

``status`` enumerates the final outcome (``succeeded``, ``error``, ``skipped``,
``cancelled``). When ``status`` is ``error``, the optional ``error`` object may
include serialized exception details captured by the runtime.

Tags & Summaries
----------------

Optional ``tags`` provide lightweight correlation metadata (for example, a
processor family or dataset identifier). ``summaries`` contain digests of inputs
and outputs when trace policy enables additional detail. Data summaries may
include hashes or representations of the :term:`Data Channel`, while context
summaries capture structured snapshots of the :term:`Context Channel` keys.

Driver Behavior
---------------

The :term:`JsonlTraceDriver` serializes each :term:`SERRecord` as one JSON line,
appending to the configured destination file. Downstream tooling can stream the
resulting :term:`Trace` and validate entries by loading the same JSON Schema.
