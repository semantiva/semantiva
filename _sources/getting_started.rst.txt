Getting Started
===============

.. _install-run-your-first-pipeline:

Install & run your first pipeline
---------------------------------
(See the steps below to install Semantiva and execute a sample pipeline.)

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

   semantiva run hello_pipeline.yaml --trace.driver jsonl --trace.option detail=all --trace.output traces/

This command will produce detailed execution traces.

Running a Pipeline from Python
------------------------------

You can load a pipeline from YAML and execute it programmatically.

.. code-block:: python

   from semantiva.pipeline import Pipeline, load_pipeline_from_yaml

   nodes = load_pipeline_from_yaml("hello_pipeline.yaml")
   p = Pipeline(nodes)
   result = p.process()  # -> :term:`Payload`

   print(result.data)     # e.g., FloatDataType(2.0)
   print(result.context)  # dict-like context object

Note that ``Pipeline.process`` always returns a :term:`Payload`.

Next Steps
----------

- :doc:`concepts`
- :doc:`pipeline`
- :doc:`studio_viewer`
- :doc:`ser`

See also
--------

For terminal usage, see :doc:`cli` for the full CLI reference.
