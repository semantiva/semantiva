Inspection Payload & CLI
========================

Inspection computes a **configuration-only** view of a pipeline. The builder
exposes a canonical payload that both the CLI and GUI consume.

.. note::
   The inspection payload is the single source of truth for GUI/CLI in
   config-only mode. It never contains runtime or run-space live identifiers.

See also :doc:`identity_cheatsheet` for a quick reference to the identities.


Payload shape
-------------

The payload returned by :func:`semantiva.inspection.build_inspection_payload`
is JSON-safe and deterministic. All ordering is canonical:

* Nodes appear in pipeline execution order.
* ``required_context_keys`` are sorted alphabetically.
* All dictionaries contributing to identity computation are key-sorted.

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
           "fqcn": "package.Class",
           "node_semantic_id": "…",
           "preprocessor_metadata": {
             "derive": {
               "parameter_sweep": {
                 "parameters_sig": {"factor": {"format": "ExpressionSigV1", "ast": "…"}},
                 "variables_sig": {"t": {"kind": "range", "lo": 0.0, "hi": 1.0, "steps": 3, "scale": "linear", "endpoint": true}},
                 "mode": "combinatorial",
                 "broadcast": false,
                 "collection": "semantiva.examples.test_utils.FloatDataCollection"
               }
             }
           }
         }
       ]
     },
     "required_context_keys": ["batch_size", "seed"]
   }

.. note::

   The ``run_space`` object contains only ``spec_id`` at inspection time.
   The ``inputs_id`` field is **never computed** during inspection—it appears
   only in runtime traces after input sources are fingerprinted.

API entry points
----------------

The inspection layer exposes three primary entry points:

* ``semantiva.inspection.build_pipeline_inspection`` — error-resilient builder
  returning ``PipelineInspection``.
* ``semantiva.inspection.build_inspection_payload`` — canonical, JSON-safe
  payload used by GUI/CLI (preferred over the legacy name).
* ``semantiva.inspection.build_canonical_graph`` — canonical graph
  representation for visualization.

.. deprecated:: 0.5.1
   ``semantiva.inspection.build`` is deprecated in favour of
   ``semantiva.inspection.build_inspection_payload`` and will be removed in a
   future minor release (not before 0.6.0). The helper
   ``semantiva.inspection.collect_required_context_keys`` is also deprecated;
   access ``PipelineInspection.required_context_keys`` directly instead.

Excluded fields
^^^^^^^^^^^^^^^

The payload never exposes runtime identifiers or UI-only metadata:

* ``pipeline_id`` (``plid-*``) — runtime-only
* ``run_id`` (``run-*``) — runtime-only
* ``run_space_launch_id`` — runtime-only
* ``run_space_attempt`` — runtime-only
* ``run_space_index`` — runtime-only
* ``run_space_context`` — runtime-only
* ``run_space_inputs_id`` — computed at runtime, **never** at inspection
* ``preprocessor_view`` — UI-only (raw expressions for display)

These exclusions ensure the payload remains a pure configuration-time artifact
suitable for caching, comparison, and use as a single source of truth (SSOT)
for configuration identity.


CLI contract
------------

``semantiva inspect <pipeline.yaml>`` renders the payload in two modes:

Concise mode (default)
^^^^^^^^^^^^^^^^^^^^^^

Prints exactly four lines of identity information:

.. code-block:: text

   Configuration Identity
   - Semantic ID: plsemid-…
   - Config ID:   plcid-…
   - Run-Space Config ID: <spec_id or "none">
   Required Context Keys: a, b, c

* ``semantic_id`` and ``config_id`` are always present.
* ``Run-Space Config ID`` shows the run-space plan fingerprint if a ``run_space``
  section exists in the YAML, otherwise displays ``none``.
* ``Required Context Keys`` lists all keys that must be provided in the initial
  payload context, sorted alphabetically.

Extended mode (``--extended``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Appends a per-node table after the concise output:

.. code-block:: text

   Nodes:
   - UUID: <node_uuid>
     Role: DataOperation
     FQCN: package.module.ClassName
     Node Semantic ID: <semantic_id or "none">
     Sweep:
       parameters_sig: arg1, arg2
       variables_sig: var1, var2
       mode: combinatorial
       broadcast: false
       collection: package.CollectionClass

For nodes with ``derive.parameter_sweep`` metadata, the sweep summary includes:

* ``parameters_sig`` — keys of swept parameters (not the full expressions or signatures)
* ``variables_sig`` — keys of sweep variables
* ``mode`` — sweep mode (e.g., ``combinatorial``, ``zip``)
* ``broadcast`` — whether broadcast is enabled
* ``collection`` — fully-qualified collection class name

**Guarantees**

* The CLI never prints runtime IDs (``plid-*``, ``run-*``, ``run_space_launch_id``, etc.).
* Raw sweep expressions (``expr`` fields) are never shown—only sanitized signatures.
* The output is deterministic and suitable for snapshot testing.

Invalid configuration parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Invalid configuration parameters are still reported after the identity block,
and ``--strict`` continues to exit non-zero when invalid parameters are present.
