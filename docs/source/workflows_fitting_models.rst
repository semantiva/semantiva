Workflows — Fitting Models via ``model:``
=========================================

Overview
--------

This workflow demonstrates fitting a simple polynomial model by configuring:

- :py:class:`semantiva.workflows.fitting_model.FittingModel`
- :py:class:`semantiva.workflows.fitting_model.PolynomialFittingModel`
- :py:class:`semantiva.workflows.fitting_model.ModelFittingContextProcessor`

The processor consumes series data from the **context channel** (independent and
dependent arrays) and writes the fitted coefficients back into the **context**.

How it works
------------

The example config uses the ``model:`` resolver to describe and instantiate a fitting
model in a single, declarative string:

- ``fitting_model: "model:PolynomialFittingModel:degree=2"`` → a 2nd-degree polynomial
- ``independent_var_key: "t_values"`` and ``dependent_var_key: "data_values"`` → names
  of context keys that must contain the x/y arrays
- ``context_keyword: "fit_coefficients"`` → where results are stored in the context

At runtime, :py:class:`~semantiva.workflows.fitting_model.ModelFittingContextProcessor`
reads the arrays from ``payload.context``, fits the model, and stores the coefficients
under ``payload.context["fit_coefficients"]``.

Run it (inspect, then execute)
------------------------------

**1) Inspect the pipeline (pre-flight checks)**

.. code-block:: bash

   semantiva inspect tests/pipeline_model_fitting.yaml --extended

You should see the canonical identities (``PipelineId``, per-node ``node_uuid``) and
the configured parameters for the fitting step. See :doc:`introspection_validation`.

**2) Execute programmatically with initial context**

This workflow expects two arrays in the context. Until CLI context injection is added,
seed them programmatically:

.. code-block:: python

   from semantiva.configurations import load_pipeline_from_yaml
   from semantiva.pipeline import Pipeline
   from semantiva.pipeline.payload import Payload

   # Toy data: y = 1 + 2 t + 0.5 t^2 (noisy-free for demo)
   t_values = [-1.0, 0.0, 1.0, 2.0]
   data_values = [1 + 2*t + 0.5*(t**2) for t in t_values]

   nodes = load_pipeline_from_yaml("tests/pipeline_model_fitting.yaml")
   p = Pipeline(nodes)

   initial = Payload(data=None, context={
       "t_values": t_values,
       "data_values": data_values,
   })
   result = p.process(initial)   # -> Payload(data=..., context=...)

   print("Coefficients:", result.context.get("fit_coefficients"))

The coefficients are written under ``fit_coefficients`` in the **context**. The data
channel for this step is pass-through.

.. note::

   A CLI flag for context injection (``--context key=value``) is **planned**; until
   then, initialize context via pipeline steps or programmatically.

**3) Visualize the config**

.. code-block:: bash

   semantiva-studio-viewer serve-pipeline tests/pipeline_model_fitting.yaml --port 8000
   # open http://127.0.0.1:8000 and click the fitting node to see its parameters and node_uuid

Link-outs:
- :doc:`pipeline` (Payload and dual channels)
- :doc:`registry_and_extensions` (``model:`` resolver and extensions)
- :doc:`studio_viewer` (serve and export diagrams)

Example YAML
------------

.. literalinclude:: ../../tests/pipeline_model_fitting.yaml
   :language: yaml

Autodoc
-------

.. automodule:: semantiva.workflows.fitting_model
   :members:
   :undoc-members:
   :show-inheritance:
