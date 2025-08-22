Pipeline (central entry point)
==============================

Overview & Mental Model
-----------------------

- Users define *processors* and YAML; **nodes are created by factories**.
- Pipelines are sequences of nodes across data/context/IO channels.

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
