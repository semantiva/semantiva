Data Processors
===============

Overview
--------

- :py:class:`semantiva.data_processors.data_processors.DataOperation`: transforms data
- :py:class:`semantiva.data_processors.data_processors.DataProbe`: inspects/records
- :py:class:`semantiva.data_processors.data_processors.OperationTopologyFactory` and slicing utilities
- :py:class:`semantiva.data_processors.parametric_sweep_factory.ParametricSweepFactory`: generate collections by sweeping parameters

Examples
--------

.. literalinclude:: ../../tests/parametric_sweep_demo.yaml
   :language: yaml
   :caption: Parametric sweep demo

Annotated walkthrough
---------------------

This example demonstrates a parametric sweep using resolvers:

1. ``sweep:FloatValueDataSource:FloatDataCollection``

   *Generates a collection by sweeping an independent variable.*

   - ``num_steps: 3`` – discretizes the range into 3 steps
   - ``independent_vars: { t: [-1, 2] }`` – defines the sweep variable and range
   - ``parametric_expressions: { value: "2.0 * t" }`` – calculates a value from ``t``

   The sweep produces a ``FloatDataCollection`` of items whose **data** results from
   the expression and whose **context** carries the sweep variable(s).

2. ``slicer:FloatCollectValueProbe:FloatDataCollection``

   *Collects values from a collection and writes them into the **context**.*

   - ``context_keyword: "sweep_results"`` – the collected values appear at
     ``payload.context["sweep_results"]``.

3. ``FloatCollectionSumOperation``

   *Aggregates the collection into a scalar sum on the **data** channel.*

4. ``FloatBasicProbe``

   *Records the final scalar into the **context**.*

   - ``context_keyword: "final_sum"`` – the scalar is stored at
     ``payload.context["final_sum"]``.

Run it
------

.. code-block:: bash

   # Validate first (shows node_uuid, parameters)
   semantiva inspect tests/parametric_sweep_demo.yaml --extended

   # Then execute
   semantiva run tests/parametric_sweep_demo.yaml -v

After execution, check logs and your context: a list at ``sweep_results`` and a
scalar ``final_sum`` should be present. Use :doc:`studio_viewer` to visualize the
graph, and :doc:`tracing` to record timings if needed.

Autodoc
-------

.. automodule:: semantiva.data_processors.data_processors
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: semantiva.data_processors.data_slicer_factory
   :members:
   :undoc-members:

.. automodule:: semantiva.data_processors.parametric_sweep_factory
   :members:
   :undoc-members:
