Pipeline (central entry point)
==============================

Overview & Mental Model
-----------------------

- Users define *processors* and YAML; **nodes are created by factories**.
- Pipelines are sequences of nodes across data/context/IO channels.

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

At load time Semantiva normalizes this YAML into a canonical *GraphV1* object.
GraphV1 guarantees deterministic identity: every node has a positional
``node_uuid`` and the entire pipeline has a ``PipelineId``. These identities
are stable across formatting or whitespace changes.

Running a Pipeline from Python
------------------------------

You can load a pipeline from YAML and execute it programmatically.

.. code-block:: python

   from semantiva.pipeline import Pipeline, load_pipeline_from_yaml

   nodes = load_pipeline_from_yaml("hello_pipeline.yaml")
   p = Pipeline(nodes)
   result = p.process()  # -> Payload(data=..., context=...)

   print(result.data)     # e.g., FloatDataType(2.0)
   print(result.context)  # dict-like context object

Note that :py:meth:`~semantiva.pipeline.pipeline.Pipeline.process` always returns a :term:`Payload`.
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
- Provide processors (see :doc:`data_processors`) and register via :doc:`registry_and_extensions`.

Parameter & Context Resolution
------------------------------

- YAML → ClassRegistry (class resolvers) + parameter resolvers.
- Context keys can be injected/renamed/deleted.

Examples
--------

.. literalinclude:: ../../tests/test_pipeline_defaults.yaml
   :language: yaml
   :caption: Pipeline default parameters

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
