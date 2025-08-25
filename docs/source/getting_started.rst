Getting Started
===============

Installation
------------

To install Semantiva, use pip:

.. code-block:: bash

   pip install semantiva

This installs the core Semantiva framework and its dependencies.

Quickstart - Hello Pipeline
-----------------------------

Save the following minimal pipeline definition to a file (e.g. ``hello_pipeline.yaml``):

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

Run it with:

.. code-block:: bash

   semantiva run hello_pipeline.yaml

This command executes the pipeline and prints out pipeline execution logs.

You can also run the pipeline with tracing enabled.

.. code-block:: bash

   semantiva run hello_pipeline.yaml --trace-driver jsonl --trace-detail all --trace-output traces/

This command will produce detailed execution traces.

Run from Python
---------------

.. code-block:: python

   from semantiva import Pipeline
   from semantiva.configurations import load_pipeline_from_yaml

   nodes = load_pipeline_from_yaml("hello_pipeline.yaml")
   p = Pipeline(nodes)
   result = p.process()  # Returns a Payload object with data and context
   print("Pipeline executed")
   print(f"Output data: {result.data}") # Prints `Output data: FloatDataType(2.0)`

Next Steps
----------

- :doc:`concepts`
- :doc:`pipeline`
- :doc:`studio_viewer`
- :doc:`tracing`
