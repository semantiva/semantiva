Getting Started
===============

Install
-------

.. code-block:: bash

   pip install -e .
   pip install sphinx

Hello, Pipeline (YAML)
----------------------

.. literalinclude:: ../../tests/simple_pipeline.yaml
   :language: yaml
   :caption: Example YAML pipeline (tests/simple_pipeline.yaml)

Run from Python
---------------

.. code-block:: python

   from semantiva import Pipeline
   from semantiva.configurations import load_pipeline_from_yaml

   nodes = load_pipeline_from_yaml("tests/simple_pipeline.yaml")
   p = Pipeline(nodes)
   result = p.run()  # Returns a Payload
   print("Pipeline executed")

Run from CLI
------------

.. code-block:: bash

   semantiva run tests/simple_pipeline.yaml

With tracing enabled:

.. code-block:: bash

   semantiva run tests/simple_pipeline.yaml --trace-driver jsonl --trace-output traces/

Next Steps
----------

- :doc:`concepts`
- :doc:`pipeline`
- :doc:`studio_viewer`
- :doc:`tracing`
