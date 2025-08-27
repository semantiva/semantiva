Examples Index
==============

.. list-table::
   :header-rows: 1

   * - Example
     - File
   * - Basic pipeline
     - ``tests/simple_pipeline.yaml``
   * - Pipeline defaults
     - ``tests/test_pipeline_defaults.yaml``
   * - Model fitting
     - ``tests/pipeline_model_fitting.yaml``
   * - Parametric sweep
     - ``tests/parametric_sweep_demo.yaml``

How to run these examples
-------------------------

**Basic pipeline**  
Inspect: ``semantiva inspect tests/simple_pipeline.yaml --extended``  
Run: ``semantiva run tests/simple_pipeline.yaml -v``

**Model fitting (tutorial)** — see :doc:`workflows_fitting_models`  
Inspect: ``semantiva inspect tests/pipeline_model_fitting.yaml --extended``  
Execute: use the Python snippet on the tutorial page to seed context; CLI context
injection is planned.

**Parametric sweep** — see :doc:`data_processors`  
Inspect: ``semantiva inspect tests/parametric_sweep_demo.yaml --extended``  
Run: ``semantiva run tests/parametric_sweep_demo.yaml -v``
