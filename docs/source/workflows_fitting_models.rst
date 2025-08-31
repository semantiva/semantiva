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
- ``context_keyword: "fit_coefficients"`` → where results are stored in the context
  (the context must provide ``x_values`` and ``y_values`` arrays)

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

**2) Execute from the CLI with initial context**

Provide arrays via ``--context`` (multiple flags allowed):

.. code-block:: bash

   semantiva run tests/pipeline_model_fitting.yaml \
     --context x_values=[-1.0,0.0,1.0,2.0] \
     --context y_values="[1.0,1.0,2.5,5.0]"

The resulting coefficients are written to ``fit_coefficients`` in the **context**.

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

.. code-block:: python

   >>> from semantiva.configurations import load_pipeline_from_yaml
   >>> from semantiva.pipeline import Pipeline
   >>> nodes = load_pipeline_from_yaml("tests/pipeline_model_fitting.yaml")
   >>> p = Pipeline(nodes)
   >>> result = p.process(payload=None)  # will fail unless you provide x_values/y_values at CLI

Autodoc
-------

.. automodule:: semantiva.workflows.fitting_model
   :members:
   :undoc-members:
   :show-inheritance:
