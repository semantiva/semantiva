Identity Cheatsheet
===================

Semantiva separates a pipeline's **meaning** (semantics), **configuration**
(instantiation), and **execution** (launch/run) into distinct identity layers.
This keeps provenance unambiguous and enables reliable comparison, caching,
and traceability.

.. contents::
   :local:
   :depth: 1


Identity Layers at a Glance
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 25 30

   * - Layer
     - Identifier
     - What it answers
     - Source
   * - **Meaning (Semantics)**
     - ``plsemid-…``
     - "Is this the same pipeline logic?"
     - YAML → canonical spec with sanitized preprocessor semantics
   * - **Configuration**
     - ``plcid-…``
     - "Is this the same configured instance?"
     - YAML → canonical configuration (parameters + sweep definitions)
   * - **Run-Space Plan**
     - ``run_space_spec_id``
     - "Is this the same launch plan?"
     - YAML → run-space section (RSCF v1)
   * - **Node (Graph)**
     - ``node_uuid``
     - "Which declared node?"
     - YAML → ``pipeline_spec_canonical.nodes[*].uuid``
   * - **Node (Semantics)**
     - ``node_semantic_id``
     - "Has this node's preprocessor changed?"
     - YAML → sanitized from ``derive.parameter_sweep``
   * - **Execution (Launch)**
     - ``plid-…``
     - "Which launch container?"
     - **Trace only** (``pipeline_start.pipeline_id``)
   * - **Execution (Run)**
     - ``run-…``
     - "Which execution attempt?"
     - **Trace only** (``trace_header.run_id``)
   * - **Run-Space Inputs**
     - ``run_space_inputs_id``
     - "Were the inputs the same?"
     - **Trace only** (RSM v1 materialization)

All identifiers above ``plid-…`` and ``run-…`` are computable from YAML at
inspection time and are deterministic. Runtime identifiers (``plid-…``,
``run-…``, ``run_space_inputs_id``) appear only in traces and are documented
in :doc:`ser` and :doc:`trace_stream_v1`.


Semantic ID (``plsemid-*``)
---------------------------

* Computed by :func:`semantiva.inspection.build` from the canonical
  GraphV1 structure.
* Includes sanitized ``derive.parameter_sweep`` metadata. Expressions are
  reduced to ``normalize_expression_sig_v1`` signatures and sweep domains are
  summarized by ``variable_domain_signature``.
* Stable under cosmetic YAML edits (whitespace, ordering) and free of runtime
  fields such as ``run_id`` or ``plid-*`` preview identifiers.
* Surfaces in the inspection payload as ``identity.semantic_id`` and is shown
  by the CLI via ``semantiva inspect``.


Config ID (``plcid-*``)
-----------------------

* Hashed across ``(node_uuid, node_semantic_id)`` pairs. Nodes without derive
  preprocessors contribute ``"none"``; sweep nodes contribute a sanitized
  fingerprint via ``compute_node_semantic_id``.
* Highlights configuration drift whenever node-level semantics change, even if
  the pipeline graph remains constant.
* Available inside the inspection payload at ``identity.config_id``.


Run-Space Plan ID
-----------------

* ``identity.run_space.spec_id`` mirrors ``run_space_spec_id`` emitted at
  runtime. It is the RSCF v1 hash of the YAML ``run_space`` declaration.
* **Inspection-time rule**: ``identity.run_space.inputs_id`` is **always omitted**
  or ``null`` during inspection (inputs require materialization and are never
  computed at configuration time).
* Runtime traces populate ``inputs_id`` when data sources are fingerprinted.


SSOT Rules & Exclusions
-----------------------

The inspection payload is the single source of truth (SSOT) for configuration
identity. It guarantees:

**Determinism**
   * Canonical node ordering from the pipeline specification.
   * ``required_context_keys`` sorted alphabetically.
   * All dictionaries contributing to identity computation are key-sorted before hashing.

**Sanitization**
   * Sweep expressions reduced to ``normalize_expression_sig_v1`` signatures.
   * Variable domains summarized by ``variable_domain_signature``.
   * No raw ``expr`` strings leak into ``pipeline_spec_canonical``.

**Exclusion List** (forbidden at inspection time)
   * ``pipeline_id`` (``plid-*``) — runtime-only (trace)
   * ``run_id`` (``run-*``) — runtime-only (trace)
   * ``run_space_launch_id`` — runtime-only (trace)
   * ``run_space_attempt`` — runtime-only (trace)
   * ``run_space_index`` — runtime-only (trace)
   * ``run_space_context`` — runtime-only (trace)
   * ``run_space_inputs_id`` — computed at runtime from materialized inputs
   * ``preprocessor_view`` — UI-only (raw expressions for display)

.. note::

   Runtime identifiers (``plid-*``, ``run-*``, and run-space live fields) are
   **never** computed during inspection. They appear only in execution traces
   and are documented in :doc:`ser` and :doc:`trace_stream_v1`.


Inspection Payload Snapshot
---------------------------

The builder returns a canonical payload used by both the CLI and the GUI.

.. code-block:: json

   {
     "identity": {
       "semantic_id": "plsemid-…",
       "config_id": "plcid-…",
       "run_space": {"spec_id": "…"}
     },
     "pipeline_spec_canonical": {
       "nodes": [
         {
           "uuid": "…",
           "role": "DataOperation",
           "fqcn": "module.Class",
           "node_semantic_id": "…",
           "preprocessor_metadata": {
             "derive": {
               "parameter_sweep": {
                 "parameters_sig": {"arg": {"format": "ExpressionSigV1", "ast": "…"}},
                 "variables_sig": {"var": {"kind": "range", "lo": 0.0, "hi": 1.0, "steps": 2, "scale": "linear", "endpoint": true}},
                 "mode": "combinatorial",
                 "broadcast": false,
                 "collection": "package.FloatDataCollection"
               }
             }
           }
         }
       ]
     },
     "required_context_keys": ["a", "b"]
   }

.. note::

   The payload intentionally omits ``inputs_id`` and all runtime identifiers
   (``run_id``, ``pipeline_id``, ``run_space_launch_id``, etc.) as well as
   UI-only metadata (``preprocessor_view``). See **SSOT Rules & Exclusions** above.


Where to Find the IDs
---------------------

* CLI: ``semantiva inspect [--extended]`` prints the payload above in a
  human-readable form.
* Python: call :func:`semantiva.inspection.build` to obtain the same
  dictionary.
* Runtime traces: ``semantic_id`` and ``config_id`` are attached to
  ``pipeline_start`` events; run-space identities appear on ``run_space_start``.
