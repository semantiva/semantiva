Pipelines in Semantiva
======================

Overview & Mental Model
-----------------------

- Users define *processors* with domain logic and configure pipelines in YAML; **nodes are created by factories**.
- Pipelines are sequences of nodes across data/context/IO channels.

.. admonition:: Who this is for

   This page is the **pipeline user guide**.
   It assumes you have completed :doc:`getting_started` and are familiar
   with the basic workflow described in :doc:`personas/pipeline_users`.

   If you are authoring new processors, also see :doc:`creating_components`
   and :doc:`personas/framework_developers`.

Defining Pipelines in YAML
--------------------------

A Semantiva pipeline is described in a YAML file using the ``pipeline:`` key. Each node
is defined under ``nodes:`` with a processor and optional parameters.

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0
       - processor: FloatMultiplyOperation
         parameters:
           factor: 2.0
       - processor: FloatTxtFileSaver
         parameters:
           path: "output_float.txt"

Each ``processor`` entry references a component (by fully qualified class name or
short name if registered). The ``parameters`` map configures that processor. Nodes
may also define ``ports`` if they connect to non-default inputs/outputs.

.. _probe-nodes:

Probe nodes
-----------

.. note::

   **Probes require a context key.** Probes observe the data channel but must
   always persist their result to the pipeline context. Configure this at the
   node level with ``context_key``-the node (not the probe) writes the returned
   value into context:

   .. code-block:: yaml

      pipeline:
        nodes:
          - processor: my.probes.DatasetEvalProbe
            context_key: metrics.eval
            parameters:
              model: my.models.Classifier

   Omitting ``context_key`` for a probe node is invalid. ``semantiva inspect``
   fails validation with a configuration error until the key is provided.

.. _pipeline-yaml-parameters-precedence:

Parameter resolution (precedence)
---------------------------------

At runtime, node parameters are resolved as:

1. Node ``parameters:`` in YAML
2. Existing ``payload.context`` values
3. Python defaults in the processor's ``_process_logic`` signature

Missing required parameters raise:

``KeyError: Unable to resolve parameter 'name' from context, node configuration, or defaults.``

Unknown configuration parameters that are not accepted by the processor are
reported during inspection and raise an error before execution.

Derive: pre-execution computation
---------------------------------

The reserved node key ``derive`` establishes the **preprocessor boundary**. 
Preprocessors under ``derive`` compute parameter values before the processor 
executes, enabling dynamic configuration based on variables, context, or other 
runtime information.

**Execution model**::

   [YAML node with derive block]
        |
        v
   derive.parameter_sweep     (resolves variables → parameter values)
        |
        v
   processor execution        (receives computed + explicit + default parameters)

**Key properties:**

* **Pre-execution**: All ``derive`` tools run before the processor is invoked.
* **Parameter computation**: Transforms variables and expressions into concrete values.
* **Transparent integration**: Computed parameters merge seamlessly with explicitly
  provided values and processor defaults.
* **Provenance tracking**: Parameter sources are recorded in trace outputs (see
  :doc:`collection_modifiers`).

The most common derive tool is ``parameter_sweep`` (see
:doc:`collection_modifiers`), which computes parameters from variables and can
produce collection outputs for data sources and operations or lists of results
for probes.

Parameter Validation in YAML Configuration
-------------------------------------------

Invalid Parameters Detected
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters in YAML configuration are validated against processor signatures:

.. code-block:: yaml

   # ❌ This will be detected as invalid
   pipeline:
     nodes:
       - processor: FloatMultiplyOperation
         parameters:
           factor: 2.0      # ✅ Valid parameter
           facotr: 3.0      # ❌ Invalid (typo)
           unknown: "test"  # ❌ Invalid (not accepted by processor)

.. note::
   The typo ``facotr`` is intentional, to demonstrate how strict validation catches misspelled parameter names.

CLI Inspection with --strict
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Report invalid parameters and exit non-zero
   semantiva inspect bad_pipeline.yaml --strict

   # Output:
   # Invalid configuration parameters:
   # - node #0 (FloatMultiplyOperation): facotr
   # - node #0 (FloatMultiplyOperation): unknown

Runtime Validation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # This will raise InvalidNodeParameterError at pipeline construction
   from semantiva.pipeline import Pipeline
   from semantiva.exceptions import InvalidNodeParameterError

   try:
       pipeline = Pipeline(configs_with_invalid_params)
   except InvalidNodeParameterError as e:
       print(f"Invalid parameters: {e.invalid}")


Canonical spec & identity
-------------------------

Pipelines are normalized into :term:`GraphV1`, producing deterministic identities:
:term:`PipelineId` for the pipeline and :term:`node_uuid` per node. See :doc:`graph`.

Running a Pipeline from Python
------------------------------

You can load a pipeline from YAML and execute it programmatically.

.. code-block:: python

   from semantiva import Pipeline, load_pipeline_from_yaml

   nodes = load_pipeline_from_yaml("hello_pipeline.yaml")
   p = Pipeline(nodes)
   result = p.process()  # -> :term:`Payload`

   print(result.data)     # e.g., FloatDataType(2.0)
   print(result.context)  # dict-like context object

Note that ``Pipeline.process`` always returns a :term:`Payload`.
There is no form that accepts separate data and context arguments.

What is a Payload?
------------------

Every pipeline step in Semantiva consumes and produces a :term:`Payload`.

A :class:`~semantiva.pipeline.payload.Payload` is a typed envelope with two channels:

* ``payload.data`` - the primary data object, a subclass of ``BaseDataType``.
* ``payload.context`` - a dictionary-like structure carrying metadata keys and values.

Together, the data and context channels flow through the pipeline, enabling
dynamic parameter injection, state propagation, and metadata logging.

Public API Surface
------------------

- :py:class:`semantiva.pipeline.pipeline.Pipeline`
- :py:class:`semantiva.pipeline.payload.Payload`

Extension Points
----------------
- Provide processors (see :doc:`data_processors`) and register via :doc:`extensions`.

.. _objects-in-pipeline-configurations:

Objects in Pipeline Configurations
----------------------------------
:term:`Resolver`\s enable declarative references to objects and values:

- ``model:PolynomialFittingModel:degree=2`` - instantiate a descriptor-backed model
- ``slice:/context/roi/window`` - pull a value from the context map
- ``rename:``, ``delete:`` - transform parameter maps

Example:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: ModelFittingContextProcessor
         parameters:
           fitting_model: "model:PolynomialFittingModel:degree=2"
           context_key: "fit_coefficients"

See :doc:`extensions` for resolver overview and best practices.

Autodoc
-------

.. automodule:: semantiva.pipeline.pipeline
   :members: Pipeline
   :undoc-members:
   :show-inheritance:

.. automodule:: semantiva.pipeline.payload
   :members: Payload
   :undoc-members:
   :show-inheritance:
