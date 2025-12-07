Introspection & Validation
==========================

Semantiva provides an **inspection pipeline** that lets you check pipelines
*before* execution and export structured inspection payloads for tooling.

Overview
--------

There are two main entry points:

- :command:`semantiva inspect` - CLI inspection with optional extended report.
- The ``semantiva.inspection`` module - Python APIs for programmatic access.

The goals are to:

- Catch configuration errors early.
- Compute and expose pipeline identities.
- Summarise required context keys.
- Provide a stable JSON payload for GUI and other tools.

Example pipeline used below
---------------------------

All examples on this page use the same minimal two-node pipeline. Save this as
``pipeline.yaml``:

.. code-block:: yaml

   extensions: ["semantiva-examples"]

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0

       - processor: FloatAddOperation
         parameters: {}

Note that ``FloatAddOperation`` declares no ``addend`` parameter in the
configuration. Instead, it must be provided via the context at runtime. This
demonstrates how inspection reports **context-dependent parameters**.

CLI usage
---------

Basic inspection:

.. code-block:: bash

   semantiva inspect pipeline.yaml

.. code-block:: console

   Configuration Identity
   - Semantic ID: plsemid-c64abfde7d72ce83e39f57caafecec632d5df806588c687efbdc5614106893c6
   - Config ID:   plcid-758b8a89c8f44207ff9de48a8c6319d7b31503ab39836ff5d92837841d209ce1
   - Run-Space Config ID: none
   Required Context Keys: addend

   Pipeline Structure:
       Required context keys: addend

       1. Node: FloatValueDataSource (DataSource)
           Parameters: value
               From pipeline configuration: value=1.0
               From processor defaults: None
               From context: None
           Context additions: None
           Invalid parameters:
           Configuration valid: True

       2. Node: FloatAddOperation (DataOperation)
           Parameters: addend
               From pipeline configuration: None
               From processor defaults: None
               From context: addend (from Initial Context)
           Context additions: None
           Invalid parameters:
           Configuration valid: True

This will:

- Load extensions and the pipeline configuration.
- Build a canonical inspection model.
- Print a summary of identities and required context keys.
- Exit with a non-zero status if validation fails and ``--strict`` is set.

Extended inspection:

.. code-block:: bash

   semantiva inspect pipeline.yaml --extended

.. code-block:: console

   Configuration Identity
   - Semantic ID: plsemid-c64abfde7d72ce83e39f57caafecec632d5df806588c687efbdc5614106893c6
   - Config ID:   plcid-758b8a89c8f44207ff9de48a8c6319d7b31503ab39836ff5d92837841d209ce1
   - Run-Space Config ID: none
   Required Context Keys: addend

   Extended Pipeline Inspection:
       Required context keys: addend

   Node 1: FloatValueDataSource (FloatValueDataSource_DataSourceNode)
     - UUID: 66732bf0-1c9f-5d36-9edc-250025dbc34e
     - Role: DataSource
     - FQCN: semantiva.examples.test_utils.FloatValueDataSource
     - Node Semantic ID: none
     - Component type: DataSource
     - Input data type: NoDataType
     - Output data type: FloatDataType
     - Parameters from pipeline configuration: value=1.0
     - Parameters from processor defaults: None
     - Parameters from context: None
     - Context additions: None
     - Context suppressions: None
     - Invalid parameters:
     - Configuration valid: True

   Node 2: FloatAddOperation (FloatAddOperation_DataOperationNode)
     - UUID: 5527124a-f20d-57f4-94cb-e4bb5e8d20f3
     - Role: DataOperation
     - FQCN: semantiva.examples.test_utils.FloatAddOperation
     - Node Semantic ID: none
     - Component type: DataOperation
     - Input data type: FloatDataType
     - Output data type: FloatDataType
     - Parameters from pipeline configuration: None
     - Parameters from processor defaults: None
     - Parameters from context: addend (from Initial Context)
     - Context additions: None
     - Context suppressions: None
     - Invalid parameters:
     - Configuration valid: True

   Footnotes:
   [FloatValueDataSource]
   Outputs a FloatDataType value.

   [FloatAddOperation]
   Add a constant to FloatDataType data.

'The extended report includes:

- Per-node details (processor reference, parameters).
- Sweep parameters and expansions.
- Context-probe information.
- Links between node identities and trace identities.

Use ``--strict`` to enforce that validation errors cause a non-zero exit code.

What is validated?
------------------

Validation checks (non-exhaustive):

- **Missing parameters** - required parameters absent from YAML.
- **Unknown processors** - processor class cannot be resolved/imported.
- **Topology/ports mismatch** - declared ports do not match available
  inputs/outputs.
- **Type compatibility** - output data type is not equal or subclass of the
  downstream input type.
- **Context probes without ``context_key``** - probes that would never update
  context.
- **Unknown / unused parameters** - configuration keys that do not map to
  processor parameters.

Using the inspection payload from Python
----------------------------------------

The inspection module can emit a stable JSON-serialisable payload:

.. code-block:: python

   from semantiva.configurations import load_pipeline_from_yaml
   from semantiva.inspection import build_inspection_payload

   cfg = load_pipeline_from_yaml("pipeline.yaml")
   payload = build_inspection_payload(cfg.nodes)

   # Serialize or hand over to GUI tooling
   import json
   print(json.dumps(payload, indent=2))

.. code-block:: console

   {
     "identity": {
       "semantic_id": "plsemid-c64abfde7d72ce83e39f57caafecec632d5df806588c687efbdc5614106893c6",
       "config_id": "plcid-758b8a89c8f44207ff9de48a8c6319d7b31503ab39836ff5d92837841d209ce1",
       "run_space": null
     },
     "pipeline_spec_canonical": {
       "nodes": [
         {
           "uuid": "66732bf0-1c9f-5d36-9edc-250025dbc34e",
           "role": "DataSource",
           "fqcn": "semantiva.examples.test_utils.FloatValueDataSource",
           "node_semantic_id": "none",
           "preprocessor_metadata": {}
         },
         {
           "uuid": "5527124a-f20d-57f4-94cb-e4bb5e8d20f3",
           "role": "DataOperation",
           "fqcn": "semantiva.examples.test_utils.FloatAddOperation",
           "node_semantic_id": "none",
           "preprocessor_metadata": {}
         }
       ]
     },
     "required_context_keys": [
       "addend"
     ]
   }

.. note:: Output shown for the two-node example pipeline above; your identities and node list will differ depending on the YAML configuration. Note that ``required_context_keys`` includes ``"addend"`` because the second node expects it from context.

The payload contains:

- Global pipeline summary (node count, topological order).
- Identity section (semantic ID, config ID, run-space config ID if present).
- Per-node entries with ports, types and processor references.
- Context-related information such as required context keys.

At a high level:

- ``identity.semantic_id`` is the pipeline **semantic identity** (``plsemid-*``),
  derived from the canonical graph structure; see :doc:`identity_cheatsheet`.
- ``identity.config_id`` is the **configuration identity** (``plcid-*``),
  hashed across ``(node_uuid, node_semantic_id)`` pairs; nodes without
  preprocessors contribute ``"none"``.
- ``identity.run_space`` is either ``null`` (no run-space declared) or a
  mapping with ``spec_id`` when a ``run_space`` block is present.
- ``pipeline_spec_canonical.nodes[*].uuid`` is the canonical node identifier
  used across inspection and traces.
- ``pipeline_spec_canonical.nodes[*].role`` and ``fqcn`` describe the
  component type (DataSource, DataOperation, etc.) and the fully-qualified
  class name of the wrapped processor.
- ``pipeline_spec_canonical.nodes[*].node_semantic_id`` fingerprints any
  **preprocessor semantics** (for example ``derive.parameter_sweep``); in this
  simple example there are no preprocessors so it is ``"none"``.
- ``pipeline_spec_canonical.nodes[*].preprocessor_metadata`` holds a
  sanitised view of sweep/derive metadata; it is empty here.
- ``required_context_keys`` lists context keys that **must be provided at
  runtime** for the pipeline to execute. In our example, ``["addend"]``
  because the second node expects the ``addend`` parameter from context.

Where to go next
----------------

- :doc:`cli` - for more examples of the ``inspect`` subcommand.
- :doc:`identity_cheatsheet` - for a detailed mapping of identities.
- :doc:`trace_graph_alignment` - for how inspection identities map to the SER.
