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

CLI usage
---------

Basic inspection:

.. code-block:: bash

   semantiva inspect pipeline.yaml

This will:

- Load extensions and the pipeline configuration.
- Build a canonical inspection model.
- Print a summary of identities and required context keys.
- Exit with a non-zero status if validation fails and ``--strict`` is set.

Extended inspection:

.. code-block:: bash

   semantiva inspect pipeline.yaml --extended

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

The payload contains:

- Global pipeline summary (node count, topological order).
- Identity section (semantic ID, config ID, run-space config ID if present).
- Per-node entries with ports, types and processor references.
- Context-related information such as required context keys.

Where to go next
----------------

- :doc:`cli` - for more examples of the ``inspect`` subcommand.
- :doc:`identity_cheatsheet` - for a detailed mapping of identities.
- :doc:`trace_graph_alignment` - for how inspection identities map to the SER.
