Examples Index
==============

Runnable examples (copy locally)
--------------------------------

.. list-table:: Self-contained pipelines
   :header-rows: 1

   * - Example
     - File
     - How to run
   * - Hello pipeline
     - ``docs/source/examples/hello_pipeline.yaml`` *(copy to your workspace)*
     - ``semantiva run hello_pipeline.yaml -v``
   * - Run space (CSV-driven)
     - ``docs/source/examples/run_space_csv.yaml`` *(uses ``docs/examples/data/runs.csv``)*
     - ``semantiva run run_space_csv.yaml -v`` *(from repo root)*

Reference snippets (non-runnable as-is)
---------------------------------------

The following YAMLs illustrate additional concepts. They rely on in-repo assets
or context setup and are provided as **snippets**:

- ``tests/simple_pipeline.yaml`` — basic pipeline structure (snippet).
- ``tests/test_pipeline_defaults.yaml`` — defaults showcase (snippet).
- ``tests/pipeline_model_fitting.yaml`` — model fitting tutorial baseline (snippet).
- ``docs/source/examples/pipeline_model_fitting_flexible.yaml`` — flexible parameters (snippet).
- ``docs/source/examples/pipeline_model_fitting_nested_path.yaml`` — nested path extraction (snippet).
- ``docs/source/examples/pipeline_model_fitting_slicer_integration.yaml`` — slice integration (snippet).
- ``docs/source/examples/pipeline_model_fitting_multiple_operations.yaml`` — multiple operations (snippet).
- ``tests/parametric_sweep_demo.yaml`` — parametric sweep demonstration (snippet).
- ``docs/source/examples/run_space_floats.yaml`` — floats run-space reference (snippet).
- ``docs/examples/run_space/csv_rows.yaml`` — CSV rows-as-runs (snippet).
- ``docs/examples/run_space/csv_columns_combinatorial.yaml`` — CSV combinatorial columns (snippet).
- ``docs/examples/run_space/block_combinatorial_two_sources.yaml`` — multi-source combinatorial plan (snippet).
