Workflows — Fitting Models via ``model:``
=========================================

Overview
--------

This workflow demonstrates fitting mathematical models to data using both traditional
and flexible parameter mapping approaches. The system provides:

- :py:class:`semantiva.workflows.fitting_model.FittingModel` — Abstract base class for fitting models
- :py:class:`semantiva.workflows.fitting_model.PolynomialFittingModel` — Concrete polynomial fitting implementation  
- :py:class:`semantiva.workflows.fitting_model.ModelFittingContextProcessor` — Context processor with flexible parameter mapping

The processor consumes data from the **context channel** and writes fitted coefficients
back into the **context**. It supports both traditional fixed parameter names
(``x_values``, ``y_values``) and flexible parameter mapping for complex data structures.

Key Features
------------

**Traditional Interface (Backward Compatible)**
  Uses standard ``x_values`` and ``y_values`` parameter names with configurable output keys.
  Maintains full compatibility with existing pipelines.

**Flexible Parameter Mapping**
  Supports custom parameter names and nested path extraction using dot notation
  (e.g., ``"gaussian_fit_parameters.std_dev_x"``). Automatically handles different
  data structure formats through dynamic processor creation.

**Data Structure Compatibility**
  - **Single dictionaries**: ``{"key": [value1, value2, ...]}``
  - **Lists of dictionaries**: ``[{"key": value1}, {"key": value2}, ...]`` (common from slice outputs)
  - **Nested structures**: Multi-level path extraction with dot notation

Traditional Usage
-----------------

The traditional approach uses the ``model:`` resolver to describe and instantiate a fitting
model in a single, declarative string:

- ``fitting_model: "model:PolynomialFittingModel:degree=2"`` → a 2nd-degree polynomial
- ``context_key: "fit_coefficients"`` → where results are stored in the context
  (the context must provide ``x_values`` and ``y_values`` arrays)

At runtime, :py:class:`~semantiva.workflows.fitting_model.ModelFittingContextProcessor`
reads the arrays from ``payload.context``, fits the model, and stores the coefficients
under ``payload.context["fit_coefficients"]``.

Flexible Parameter Mapping
--------------------------

When ``independent_var_key`` and/or ``dependent_var_key`` parameters are specified,
the system automatically creates a specialized processor that can extract data using
custom parameter names and nested paths.

**Configuration Examples**

Basic flexible parameter mapping:

.. literalinclude:: examples/pipeline_model_fitting_flexible.yaml
   :language: yaml

Nested path extraction:

.. literalinclude:: examples/pipeline_model_fitting_nested_path.yaml
   :language: yaml

Slicer integration:

.. literalinclude:: examples/pipeline_model_fitting_slicer_integration.yaml
   :language: yaml

Multiple fitting operations:

.. literalinclude:: examples/pipeline_model_fitting_multiple_operations.yaml
   :language: yaml

**Data Structure Examples**

The flexible parameter mapping supports various data structure formats:

*Single Dictionary Format:*

.. code-block:: python

   data = {
       "t_values": [1.0, 2.0, 3.0, 4.0, 5.0],
       "gaussian_fit_parameters": {
           "std_dev_x": [0.1, 0.2, 0.3, 0.4, 0.5],
           "std_dev_y": [0.15, 0.25, 0.35, 0.45, 0.55],
           "angle": [10, 15, 20, 25, 30]
       }
   }

*List of Dictionaries Format (Slicer Output):*

.. code-block:: python

   data = {
       "t_values": [1.0, 2.0, 3.0, 4.0, 5.0],
       "gaussian_fit_parameters": [
           {"std_dev_x": 0.1, "std_dev_y": 0.15, "angle": 10},
           {"std_dev_x": 0.2, "std_dev_y": 0.25, "angle": 15},
           {"std_dev_x": 0.3, "std_dev_y": 0.35, "angle": 20},
           {"std_dev_x": 0.4, "std_dev_y": 0.45, "angle": 25},
           {"std_dev_x": 0.5, "std_dev_y": 0.55, "angle": 30}
       ]
   }

Integration with Pipeline Components
------------------------------------

**Slicer Integration**

The flexible parameter mapping is particularly useful when working with slice outputs.
The system automatically detects and handles data from slice aggregators:

.. code-block:: yaml

   - processor: SliceAggregatorContextProcessor
     parameters:
       # ... slice configuration
       
   - processor: ModelFittingContextProcessor
     parameters:
       fitting_model: "model:PolynomialFittingModel:degree=1"
       independent_var_key: "slice_indices"
       dependent_var_key: "aggregated_data.mean_values"
       context_key: "trend_analysis"

**Multiple Fitting Operations**

You can perform multiple fits on different aspects of the same data by configuring
multiple processors with different dependent variable paths:

.. code-block:: yaml

   # Fit standard deviation trend
   - processor: ModelFittingContextProcessor
     parameters:
       fitting_model: "model:PolynomialFittingModel:degree=1"
       independent_var_key: "t_values"
       dependent_var_key: "gaussian_fit_parameters.std_dev_x"
       context_key: "std_dev_trend"

   # Fit orientation trend
   - processor: ModelFittingContextProcessor
     parameters:
       fitting_model: "model:PolynomialFittingModel:degree=1"
       independent_var_key: "t_values"
       dependent_var_key: "gaussian_fit_parameters.angle"
       context_key: "orientation_trend"

Technical Implementation
------------------------

**Automatic Factory Selection**

When the pipeline node factory detects ``independent_var_key`` and/or ``dependent_var_key``
parameters in a ModelFittingContextProcessor configuration, it automatically:

1. Creates a specialized processor class using :py:func:`~semantiva.workflows.fitting_model._model_fitting_processor_factory`
2. Configures the processor to expect the specified parameter names
3. Sets up nested path extraction for the dependent variable
4. Maintains all standard functionality (output keys, error handling, etc.)

**Nested Path Resolution**

The system uses dot notation to traverse nested structures:

- ``"data.field"`` → ``data["field"]`` or ``data.field``
- ``"measurements.values"`` → ``measurements["values"]`` or ``measurements.values``
- Works with both dictionary access and attribute access

**Error Handling**

The system provides comprehensive error handling for:

- Missing parameters (clear error messages for required parameters)
- Invalid paths (detailed path resolution errors with context)
- Data type mismatches (validation of expected data structures)
- Empty data (handling of edge cases with empty or null data)

Run it (inspect, then execute)
------------------------------

**1) Inspect the pipeline (pre-flight checks)**

Traditional usage:

.. code-block:: bash

   semantiva inspect tests/pipeline_model_fitting.yaml --extended

Flexible parameter mapping:

.. code-block:: bash

   semantiva inspect tests/pipeline_model_fitting_flexible.yaml --extended
   semantiva inspect tests/pipeline_model_fitting_nested_path.yaml --extended

You should see the canonical identities (``PipelineId``, per-node ``node_uuid``) and
the configured parameters for the fitting step. See :doc:`introspection_validation`.

**2) Execute from the CLI with initial context**

Traditional usage (provide arrays via ``--context``):

.. code-block:: bash

   semantiva run tests/pipeline_model_fitting.yaml \
     --context x_values=[-1.0,0.0,1.0,2.0] \
     --context y_values="[1.0,1.0,2.5,5.0]"

Flexible parameter mapping:

.. code-block:: bash

   semantiva run tests/pipeline_model_fitting_flexible.yaml \
     --context time_values=[0,1,2,3,4] \
     --context measurements="[1.1,1.9,3.1,3.9,5.1]"

Nested path example:

.. code-block:: bash

   semantiva run tests/pipeline_model_fitting_nested_path.yaml \
     --context t_values=[1,2,3,4,5] \
     --context 'gaussian_fit_parameters={"std_dev_x":[0.1,0.2,0.3,0.4,0.5]}'

The resulting coefficients are written to the specified context keyword.

**3) Visualize the config**

.. code-block:: bash

   semantiva-studio-viewer serve-pipeline tests/pipeline_model_fitting.yaml --port 8000
   # open http://127.0.0.1:8000 and click the fitting node to see its parameters and node_uuid

Link-outs:
- :doc:`pipeline` (Payload and dual channels)
- :doc:`extensions` (``model:`` resolver and extensions)
- :doc:`studio_viewer` (serve and export diagrams)
- :doc:`context_processors` (Context processor fundamentals)
- :doc:`data_processors` (Data slice integration)

Example YAML Configurations
---------------------------

**Traditional Usage**

.. literalinclude:: ../../tests/pipeline_model_fitting.yaml
   :language: yaml

**Flexible Parameter Mapping**

.. literalinclude:: examples/pipeline_model_fitting_flexible.yaml
   :language: yaml

**Nested Path Extraction**

.. literalinclude:: examples/pipeline_model_fitting_nested_path.yaml
   :language: yaml

**Slicer Integration**

.. literalinclude:: examples/pipeline_model_fitting_slicer_integration.yaml
   :language: yaml

**Multiple Operations**

.. literalinclude:: examples/pipeline_model_fitting_multiple_operations.yaml
   :language: yaml

Programmatic Usage
------------------

.. code-block:: python

   >>> from semantiva import load_pipeline_from_yaml
   >>> from semantiva.pipeline import Pipeline
   >>> 
   >>> # Traditional usage
   >>> nodes = load_pipeline_from_yaml("tests/pipeline_model_fitting.yaml")
   >>> p = Pipeline(nodes)
   >>> # Requires x_values/y_values in context
   >>> 
   >>> # Flexible parameter mapping
   >>> nodes = load_pipeline_from_yaml("tests/pipeline_model_fitting_flexible.yaml")
   >>> p = Pipeline(nodes)
   >>> # Requires time_values/measurements in context
   >>> 
   >>> # Using the factory directly
   >>> from semantiva.workflows.fitting_model import _model_fitting_processor_factory
   >>> ProcessorClass = _model_fitting_processor_factory(
   ...     independent_var_key="time",
   ...     dependent_var_key="data.measurements",
   ...     context_key="analysis_results"
   ... )
   >>> processor = ProcessorClass()

API Reference
-------------

.. autofunction:: semantiva.workflows.fitting_model._model_fitting_processor_factory

Autodoc
-------

.. automodule:: semantiva.workflows.fitting_model
   :members:
   :undoc-members:
   :show-inheritance:
