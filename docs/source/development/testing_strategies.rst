Testing Strategies and Best Practices
=====================================

This page focuses on **practical** testing approaches that work well with
Semantiva's execution model. It keeps tests close to real usage and avoids
depending on internal details.

Recommended layers
------------------

1. **Pipeline-based testing (recommended)**  
   Exercise components through a small pipeline defined in YAML or Python.

2. **Node-based testing (conditional)**  
   Useful when you need to check a processor in isolation, but still construct
   it via the public factory or registry mechanisms.

3. **Unit testing of utilities (limited scope)**  
   For small, pure helper functions that do not depend on the framework.

Pipeline-based testing
----------------------

This is the most robust approach because it tests:

- Parameter resolution from configuration and context.
- Interactions between processors.
- Contracts enforced by inspection and validation.

Example: simple pipeline test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from semantiva.configurations import PipelineConfig
   from semantiva.core import Payload, ContextType
   from semantiva.pipeline import Pipeline

   def test_my_pipeline_round_trip():
       cfg = {
           "pipeline": {
               "nodes": [
                   {"processor": "FloatValueDataSource",
                    "parameters": {"value": 1.0}},
                   {"processor": "FloatAddOperation",
                    "parameters": {"addend": 2.0}},
               ]
           }
       }

       pipeline = Pipeline.from_dict(cfg)
       result = pipeline.process(Payload(data=None, context=ContextType()))

       assert result.data.value == 3.0

YAML-based configuration tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For extensions, it is often more natural to keep test examples as YAML:

.. code-block:: python

   import io
   from semantiva.configurations import load_pipeline_from_yaml
   from semantiva.core import Payload, ContextType

   def test_extension_pipeline(tmp_path):
       yaml_text = '''
       extensions: ["your-extension"]

       pipeline:
         nodes:
           - processor: YourProcessor
             parameters:
               param1: "value1"
       '''
       path = tmp_path / "config.yaml"
       path.write_text(yaml_text)

       pipeline = load_pipeline_from_yaml(str(path))
       result = pipeline.process(Payload(data=None, context=ContextType()))

       assert result.context.get_value("your.result.key") == "expected"

Node-based testing
------------------

Occasionally you may need to instantiate a processor directly. In that case:

- Use the public processor class, not internal helpers.
- Pass a realistic data type instance.
- When context is involved, construct a real context object and exercise the
  processor via its public methods.

Example:

.. code-block:: python

   from semantiva.data_types import BaseDataType

   class FloatDataType(BaseDataType[float]):
       """Simple float wrapper."""

   def test_add_operation_direct():
       op = AddConstant(addend=2.0)
       out = op.process(FloatDataType(1.0))
       assert out.data == 3.0

What to avoid
-------------

- Over-mocking core infrastructure (nodes, observers, executors).
- Reaching into private attributes to check behaviour.
- Depending on internal modules whose names start with ``_`` – those are
  implementation details and may change without notice.

Instead, prefer to:

- Assert on payloads (data and context) at well-defined points.
- Use :command:`semantiva inspect` and :command:`semantiva dev lint` in
  separate tests or CI jobs to validate configuration and contracts.
