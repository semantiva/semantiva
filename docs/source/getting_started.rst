Getting Started
===============

This page walks you from **installation** to running your **first pipeline**.

Install Semantiva
-----------------

Semantiva requires Python 3.10+.

Install from PyPI:

.. code-block:: bash

   pip install semantiva

Then verify that the CLI is available:

.. code-block:: bash

   semantiva --help

Quickstart - Hello pipeline (YAML only)
---------------------------------------

The smallest useful example is a pipeline defined purely in YAML and executed
from the CLI. Create a file ``hello.yaml``:

.. code-block:: yaml

   extensions: ["semantiva-examples"]  # or your own extension packages

   pipeline:
     nodes:
       - processor: FloatValueDataSource
         parameters:
           value: 1.0

       - processor: FloatAddOperation
         parameters:
           addend: 2.0

       - processor: FloatMultiplyOperation
         parameters:
           factor: 10.0

       - processor: FloatCollectValueProbe
         context_key: "result"
       - processor: template:"result_{result}.txt":path
       - processor: FloatTxtFileSaver

Run the pipeline:

.. code-block:: bash

   semantiva run hello.yaml

The fourth node writes into the context key ``result``, which is used to define the
output file path in the fifth node. The last node saves the final float value to
that file.

Running the same pipeline from Python
-------------------------------------

You can run the same configuration programmatically. The **pipeline
configuration** is still the single source of truth - your Python code just
loads and executes it.

.. code-block:: python

   from semantiva.configurations import load_pipeline_from_yaml
   from semantiva.core import Payload, ContextType

   pipeline = load_pipeline_from_yaml("hello.yaml")

   payload = Payload(data=None, context=ContextType())
   result = pipeline.process(payload)

   print(result.context.get_value("result"))

Run-space: multiple runs from one definition
--------------------------------------------

Instead of calling the CLI in a loop with different ``--context`` values,
you can describe a *grid* of runs using a ``run_space`` block in the same
YAML file.

A minimal example:

.. code-block:: yaml

   run_space:
     combine: combinatorial
     max_runs: 20
     dry_run: false
     blocks:
       - mode: by_position
         context:
           value:  [1.0, 2.0, 3.5]
           factor: [10.0, 20.0, 30.0]
           addend: [1.0, 1.0, 1.0]

   pipeline:
     # same nodes as before ...

Then:

.. code-block:: bash

   semantiva run run_space_demo.yaml

Semantiva will expand the blocks into individual runs, each with a concrete
set of context keys. All runs share a **run-space configuration ID** and
each run has its own **run ID**, which you can see in the trace stream.

CSV-driven run-spaces and more advanced patterns are covered in
:doc:`tutorials/run_space_quickstart`.

Next steps
----------

For a deeper understanding of the model:

- :doc:`concepts` — Basic concepts and the dual data/context channel
- :doc:`pipeline` — Pipelines and nodes
- :doc:`cli` — CLI usage patterns

When you care about provenance and inspection, continue with:

- :doc:`ser`
- :doc:`trace_stream_v1`
