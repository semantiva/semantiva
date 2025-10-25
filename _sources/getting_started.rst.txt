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

Create ``hello_pipeline.yaml`` with the following contents:

.. code-block:: yaml

   extensions: ["semantiva-examples"]

   trace:
     driver: jsonl
     output_path: ./trace

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 2.0
       - processor: FloatAddOperation
         parameters:
           addend: 1.0
       - processor: FloatMultiplyOperation
         parameters:
           factor: 10.0
       - processor: FloatCollectValueProbe
         context_key: "result"
       - processor: template:"result_{result}.txt":path
       - processor: FloatTxtFileSaver

Run the pipeline:

.. code-block:: bash

   semantiva run hello_pipeline.yaml -v

This command executes the pipeline, emits JSONL SER traces in ``./trace``, and
writes the computed result to ``result_<value>.txt``.

Run-Space with CSV input
------------------------

Create ``runs.csv`` alongside ``run_space_csv.yaml``:

.. code-block:: text

   value,factor,addend
   1.0,10.0,1.0
   2.0,20.0,1.0
   3.5,30.0,1.0

.. code-block:: yaml

   extensions: ["semantiva-examples"]

   run_space:
     blocks:
       - mode: by_position
         source:
           format: csv
           path: ./runs.csv
           select: [value, factor, addend]

   trace:
     driver: jsonl
     output_path: ./trace_csv
     options:
      detail: all

   pipeline:
     nodes:
       - processor: FloatValueDataSource
       - processor: FloatAddOperation
       - processor: FloatMultiplyOperation
       - processor: FloatCollectValueProbe
         context_key: "result"
       - processor: template:"{value}_plus_{addend}_times_{factor}_equals_{result}.txt":path
       - processor: FloatTxtFileSaver

Run it with:

.. code-block:: bash

   semantiva run run_space_csv.yaml -v

Each row in ``runs.csv`` launches a run-space execution that emits SER traces in
``./trace_csv`` and writes the formatted result file for that run.

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

Next Steps
----------

- :doc:`concepts`
- :doc:`pipeline`
- :doc:`studio_viewer`
- :doc:`ser`

See also
--------

For terminal usage, see :doc:`cli` for the full CLI reference.
