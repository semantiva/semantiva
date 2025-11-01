Derive Parameter Sweep
======================

Objective
---------
This page documents **derive-based parameter sweeps** — the mechanism that
**computes processor parameters before execution** and **expands** a node into
multiple runs when variables enumerate more than one value.

Key Idea
--------
Under a node, the reserved preprocessor boundary ``derive`` hosts named
preprocessors. The **parameter_sweep** preprocessor computes **call-time
parameters** from **variables** and (optionally) expands the run-space.

**Parameters first, Variables second:**

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         derive:
           parameter_sweep:
             parameters:
               value: 2.0 * t
             variables:
               t: { lo: -1.0, hi: 2.0, steps: 3 }
             mode: combinatorial
             broadcast: false
             collection: FloatDataCollection

What it does
------------
- **Computes** the parameter ``value`` from an expression using variable ``t``.
- **Expands** into a collection typed by ``collection`` (DataSource/DataOperation).
- **Publishes** ``t_values`` in the context.

Supported kinds
---------------
- **DataSource** → generates a collection via repeated ``get_data(...)``
- **DataOperation** → augmentation-style expansion via repeated ``process(data, ...)``
- **DataProbe** → returns a **list** of probe results (no ``collection``); probe nodes
  persist via ``context_key`` (node-level) and pass-through input

YAML Reference (inside ``derive.parameter_sweep``)
--------------------------------------------------
- ``parameters`` (mapping; **required**): computed call-args (expressions).
  Keys **must** match callee argument names.
- ``variables`` (mapping; **required**): variable definitions used by expressions.
  - Range: ``{ lo: <float>, hi: <float>, steps: <int> [, scale: linear|log] }``
  - Sequence: ``[v1, v2, ...]``
  - FromContext: ``{ from_context: <key> }`` (must yield a non-empty sequence)
- ``collection`` (string; **required for DataSource/DataOperation**, **forbidden for DataProbe**)
- ``mode``: ``combinatorial`` (default) or ``by_position``
- ``broadcast``: boolean (default ``false``)

Merge semantics
---------------

.. list-table::
   :header-rows: 1

   * - Source
     - Meaning
   * - ``derive.parameter_sweep.parameters``
     - **Computed** values for callee args
   * - ``node.parameters``
     - **Provided** literals/resolvers for others
   * - callee defaults
     - Used when neither computed nor provided

If the same name appears in both places, **computed wins**.

Modes & failure cases
---------------------
- ``combinatorial``: Cartesian product across variables.
- ``by_position``: zip-style alignment. **Error** if variable sequences have
  different lengths.
- **Probe** sweeps **must not** declare ``collection``.
- **Unknown parameter names** in ``parameters`` → hard error with the callee’s signature.


Examples
--------
**DataSource**

.. code-block:: yaml

   - processor: FloatValueDataSource
     derive:
       parameter_sweep:
         parameters:
           value: 2.0 * t
         variables:
           t: { lo: -1.0, hi: 2.0, steps: 3 }
         collection: FloatDataCollection

**DataOperation (augmentation)**

.. code-block:: yaml

   - processor: FloatMultiplyOperation
     derive:
       parameter_sweep:
         parameters:
           factor: f
         variables:
           f: { lo: 1.0, hi: 3.0, steps: 3 }
         mode: by_position
         collection: FloatDataCollection

**DataProbe**

.. code-block:: yaml

   - processor: FloatCollectValueProbe
     derive:
       parameter_sweep:
         parameters: {}
         variables:
           n: { lo: 1, hi: 3, steps: 3 }
     context_key: probe_values

**FromContext: Runtime Sequence Discovery**

The ``FromContext`` variable specification enables sweeps over sequences that
are discovered or computed earlier in the pipeline. This is useful for dynamic
workflows where sweep values depend on runtime conditions or previous processing
results.

.. code-block:: yaml

   - processor: FloatValueDataSource
     derive:
       parameter_sweep:
         parameters:
           value: float(input_value)
         variables:
           input_value: { from_context: discovered_values }
         collection: FloatDataCollection

**Requirements:**

- The context key must exist at runtime and contain a non-empty, non-string sequence
- The sweep processor exposes the context key via ``get_context_requirements()`` for inspection
- A ``{var}_values`` context entry is created (e.g., ``input_value_values``) containing the
  materialized sequence for downstream use

**Example usage with CLI:**

.. code-block:: bash

   semantiva run from_context_sweep_demo.yaml --context discovered_values='[1.3, 2.5, 3.7]'

This pattern supports workflows where:

- File lists are discovered via directory scanning
- Parameter sets are loaded from configuration files
- Previous pipeline stages produce candidate values for downstream sweeps

Inspection
----------
Inspection surfaces which parameters were **computed**, **provided**,
**defaulted**, or remain **required_external_parameters** (unbound callee args
you still need to provide). See :doc:`pipeline` for inspection details.

Parameter Provenance Tracking
------------------------------

Semantiva records complete provenance for all processor parameters in the
Semantic Execution Record (SER) trace format, enabling full traceability of
parameter origins for auditing, debugging, and reproducibility.

**Provenance Mechanisms**

Each SER record contains two complementary fields in the ``processor`` section:

1. ``parameters``: The actual runtime values used for execution
2. ``parameter_sources``: The origin of each parameter value

**Parameter Source Classification**

Every parameter is tagged with one of three source types:

.. list-table::
   :header-rows: 1

   * - Source Type
     - Origin
     - Example
   * - ``"node"``
     - Declared in YAML ``parameters`` or ``derive.parameter_sweep.parameters``
     - ``factor: 2.0`` in node config
   * - ``"context"``
     - Read from pipeline context (including ``FromContext`` variables)
     - ``{ from_context: discovered_values }``
   * - ``"default"``
     - Processor's ``get_default_params()`` fallback
     - ``defaulted: 3.0`` when not provided

**SER Trace Example**

.. code-block:: json

   {
     "record_type": "ser",
     "processor": {
       "ref": "semantiva.examples.test_utils.FloatMultiplyOperation",
       "parameters": {
         "factor": 2.0,
         "from_ctx": 5.0,
         "defaulted": 3.0
       },
       "parameter_sources": {
         "factor": "node",
         "from_ctx": "context",
         "defaulted": "default"
       }
     },
     "context_delta": {
       "created_keys": ["t_values"],
       "read_keys": ["from_ctx"],
       "updated_keys": []
     }
   }

**FromContext Variable Provenance**

When using ``FromContext`` specifications, provenance tracking includes:

- **Pre-execution**: ``get_required_external_parameters()`` exposes context dependencies
  during inspection
- **Runtime**: The context key is recorded in ``context_delta.read_keys``
- **Materialization**: Created sequences appear in ``context_delta.created_keys`` as
  ``{var}_values`` (e.g., ``t_values``)
- **Parameter source**: The resolved variable value is tagged as ``"context"``

**Sweep-Generated Context Entries**

Parameter sweeps publish ``{var}_values`` sequences to the context for each variable.
These entries enable downstream processors or subsequent sweeps to access the
computed parameter sets:

.. code-block:: python

   # After sweep execution with variable 't'
   assert "t_values" in context.keys()
   # Contains: [lo, ..., hi] based on variable spec

**Provenance Benefits**

1. **Reproducibility**: Exact parameter values and origins are preserved
2. **Debugging**: Trace parameter resolution back to YAML config or context
3. **Auditing**: Distinguish configured values from runtime-discovered values
4. **Inspection**: Identify missing context requirements before execution

See :doc:`ser` for complete SER record structure and schema details.