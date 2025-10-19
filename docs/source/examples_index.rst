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
   * - Model fitting (traditional)
     - ``tests/pipeline_model_fitting.yaml``
   * - Model fitting (flexible parameters)
     - ``docs/source/examples/pipeline_model_fitting_flexible.yaml``
   * - Model fitting (nested paths)
     - ``docs/source/examples/pipeline_model_fitting_nested_path.yaml``
   * - Model fitting (slice integration)
     - ``docs/source/examples/pipeline_model_fitting_slicer_integration.yaml``
   * - Model fitting (multiple operations)
     - ``docs/source/examples/pipeline_model_fitting_multiple_operations.yaml``
   * - Parametric sweep
     - ``tests/parametric_sweep_demo.yaml``
   * - Run space (floats)
     - ``docs/source/examples/run_space_floats.yaml``
   * - Run space (CSV rows-as-runs)
     - ``docs/examples/run_space/csv_rows.yaml``
   * - Run space (CSV columns combinatorial)
     - ``docs/examples/run_space/csv_columns_combinatorial.yaml``
   * - Run space (two sources combinatorial)
     - ``docs/examples/run_space/block_combinatorial_two_sources.yaml``

How to run these examples
-------------------------

**Basic pipeline**  
Inspect: ``semantiva inspect tests/simple_pipeline.yaml --extended``  
Run: ``semantiva run tests/simple_pipeline.yaml -v``

**Model fitting (tutorial)** — see :doc:`workflows_fitting_models`  
Inspect: ``semantiva inspect tests/pipeline_model_fitting.yaml --extended``  
Execute: use the Python snippet on the tutorial page to seed context; CLI context
injection is planned.

**Model fitting (flexible parameters)** — see :doc:`workflows_fitting_models`  
Advanced model fitting with custom parameter names and flexible data structures.
Inspect: ``semantiva inspect docs/source/examples/pipeline_model_fitting_flexible.yaml --extended``

**Model fitting (nested paths)** — see :doc:`workflows_fitting_models`  
Demonstrates nested path extraction using dot notation for complex data structures.
Inspect: ``semantiva inspect docs/source/examples/pipeline_model_fitting_nested_path.yaml --extended``

**Model fitting (slice integration)** — see :doc:`workflows_fitting_models`
Shows integration with slice outputs and aggregated data processing.
Inspect: ``semantiva inspect docs/source/examples/pipeline_model_fitting_slicer_integration.yaml --extended``

**Model fitting (multiple operations)** — see :doc:`workflows_fitting_models`  
Demonstrates multiple fitting operations on different aspects of the same data.
Inspect: ``semantiva inspect docs/source/examples/pipeline_model_fitting_multiple_operations.yaml --extended``

**Parametric sweep** — see :doc:`data_processors`  
Inspect: ``semantiva inspect tests/parametric_sweep_demo.yaml --extended``  
Run: ``semantiva run tests/parametric_sweep_demo.yaml -v``
