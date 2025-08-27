Introspection & Validation
==========================

- Build inspections, summarize, export JSON, validate.

You can perform pre-execution checks from the terminal; see :doc:`cli` (subcommand **inspect**).

Examples
--------

.. code-block:: python

   from semantiva.inspection.reporter import json_report
   # Assume p is a Pipeline instance
   report = json_report(p)
   print(report)

CLI Inspection
--------------

Use the CLI to parse and validate a pipeline before executing it.

.. code-block:: bash

   # Basic inspection: parse YAML, build canonical :term:`GraphV1`, run basic checks
   semantiva inspect my_pipeline.yaml

   # Extended inspection: include node identities, ports, inferred types (where available)
   semantiva inspect my_pipeline.yaml --extended

What to expect
~~~~~~~~~~~~~~

* A summary of the pipeline (number of nodes, topological order).
* The canonical :term:`PipelineId` (deterministic across formatting changes).
* For ``--extended``:
  * Each node’s processor (FQCN or registered name).
  * The positional :term:`node_uuid` from :term:`GraphV1`.
  * Declared **ports** (if any) and parameter snapshot.
  * Any inferred or declared **input/output** types the validator can derive.

If a configuration problem is found, inspection exits non-zero and prints a structured error (see **Common Validation Errors** below).

Python APIs for Introspection
-----------------------------

For programmatic use, generate a JSON summary from a :class:`~semantiva.pipeline.pipeline.Pipeline`.

.. code-block:: python

   from semantiva.inspection.reporter import json_report
   # assume p is a Pipeline instance (built from YAML or programmatically)
   summary = json_report(p)   # -> python dict or JSON-serializable structure
   print(summary)

Typical fields present in the JSON summary:

* ``pipeline_id`` - the deterministic :term:`PipelineId` (see :doc:`graph`).
* ``nodes`` - list of nodes with:
  * ``node_uuid`` - positional identity from :term:`GraphV1`
  * ``processor`` - fully qualified class name
  * ``parameters`` - normalized parameter map
  * ``ports`` - declared input/output ports (if present)
* ``issues`` - list of warnings/errors detected by the validator

JSON Outline Example
--------------------

Below is a truncated outline of the JSON structure produced by
:func:`semantiva.inspection.reporter.json_report`. Field names shown here are
stable; values are illustrative.

.. code-block:: json

   {
     "pipeline_id": "plid-033c3704...300e",
     "nodes": [
       {
         "index": 0,
         "node_uuid": "2bd52eb9-9556-5663-b633-b69c9418f3ab",
         "processor": "FloatMockDataSource",
         "parameters": {},
         "ports": {}
       },
       {
         "index": 1,
         "node_uuid": "eb3e87c0-97b7-5097-8214-b53b4ba0fd6e",
         "processor": "FloatMultiplyOperation",
         "parameters": {"factor": 2.0},
         "ports": {}
       }
     ],
     "issues": []
   }

*Note:* If you need to reference these identities elsewhere (e.g., in trace logs),
see :doc:`trace_graph_alignment`.

.. code-block:: python

   from semantiva.pipeline import Pipeline, load_pipeline_from_yaml
   from semantiva.inspection.reporter import json_report
   p = Pipeline(load_pipeline_from_yaml("tests/hello_pipeline.yaml"))
   report = json_report(p)
   assert "pipeline_id" in report and "nodes" in report

Linking Reports to GraphV1 Identities
-------------------------------------

Inspection always works over the canonical :term:`GraphV1` representation.
That means the :term:`PipelineId` and every node’s ``node_uuid`` shown in
inspection output match the values in:

* the canonical spec (see :doc:`graph`), and
* runtime trace records (see :doc:`trace_graph_alignment`).

This identity contract lets you compare results across machines, builds, and formats.

Common Validation Errors
------------------------

Here are representative issues the validator can flag:

* **Missing parameter** - a required parameter is absent in the YAML.
* **Unknown processor** - the specified processor class cannot be resolved/imported.
* **Topology/ports mismatch** - the declared ports do not match available outputs/inputs.
* **Type incompatibility** - an upstream node’s output type is incompatible with the next node’s expected input type.

Example output (truncated):

.. code-block:: text

   ERROR: PipelineConfigurationError
   details:
     node_index: 2
     node_uuid: "eb3e87c0-97b7-5097-8214-b53b4ba0fd6e"
     processor: "TransformData"
     reason: "Incompatible types: expected ImageType, received TextType from previous node"
     hint: "Check the output of node 1 or insert a converter operation."

Tips
----

* Use ``--extended`` to include identities and port/type summaries for faster debugging.
* If resolving classes from your own packages, ensure they are importable (installed in the environment).
* Increase verbosity with ``-v`` to see more details during inspection (see :doc:`logger`).

.. _spec-phase-vs-runtime-vs-execution:

Validation Phases
-----------------

Semantiva applies checks at three moments:

* **Spec-phase (pre-run)** - when parsing YAML and building :term:`GraphV1`:
  * missing parameters, unknown processors, invalid ports/topology.
  * surfaced via ``semantiva inspect`` and during pipeline load.

* **Runtime (initialization)** - after classes are resolved and nodes are realized:
  * parameter coercion/normalization errors, environment/import issues.
  * surfaced when constructing the :class:`~semantiva.pipeline.pipeline.Pipeline`.

* **Execution (process)** - during node operation on a :class:`~semantiva.pipeline.payload.Payload`:
  * actual input/output type contracts, context key requirements, invariant checks.
  * surfaced with node identity (:term:`node_uuid`) to support precise debugging and tracing.

Troubleshooting Checklist
~~~~~~~~~~~~~~~~~~~~~~~~~

* Re-run with ``semantiva inspect --extended`` to confirm identities and topology.
* Increase log verbosity (``-v``/``-vv``) and capture the first error.
* Check :doc:`exceptions` for common error classes and meanings.
* If the failure mentions a custom processor, ensure your package is installed and importable.

Autodoc
-------

.. automodule:: semantiva.inspection.builder
   :members:
   :undoc-members:

.. automodule:: semantiva.inspection.reporter
   :members:
   :undoc-members:

.. automodule:: semantiva.inspection.validator
   :members:
   :undoc-members:
