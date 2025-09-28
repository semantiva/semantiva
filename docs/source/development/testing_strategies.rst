Testing Strategies and Best Practices
=====================================

This document outlines recommended testing approaches for Semantiva components, with particular emphasis on avoiding internal API usage and following framework patterns.

Overview
--------

Semantiva provides multiple approaches for testing components. The choice of testing strategy depends on the component type and testing goals:

1. **Pipeline-based testing** (Recommended) - Tests components through pipeline execution
2. **Node-based testing** (Conditional) - Direct processor testing with proper observers
3. **Unit testing** (Limited scope) - Testing isolated utility functions

.. warning::
   Avoid direct instantiation of internal APIs like ``_ContextObserver`` or ``_ValidatingContextObserver`` in tests. These are framework internals and their usage patterns may change.

Pipeline-Based Testing (Recommended)
-------------------------------------

Pipeline-based testing is the preferred approach for most scenarios as it:

- Tests real usage patterns that users will experience
- Exercises the full component lifecycle including validation and parameter resolution
- Provides clear expectations about results in the final payload context
- Remains stable as internal implementation details change

Example: Testing Context Processors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_processor_through_pipeline():
       """Test processor behavior through pipeline execution."""
       config = {
           "extensions": ["your_extension"],
           "pipeline": {
               "nodes": [
                   {
                       "processor": "YourProcessor",
                       "parameters": {
                           "param1": "value1",
                           "param2": "value2"
                       }
                   }
               ]
           }
       }
       
       pipeline = Pipeline.from_dict(config)
       initial_payload = Payload(data=test_data, context=ContextType())
       result_payload = pipeline.process(initial_payload)
       
       # Check results in final context
       expected_value = result_payload.context.get_value("your.key")
       assert expected_value == expected_result

Example: YAML-Based Configuration Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_yaml_configuration():
       """Test component using YAML configuration (closest to real usage)."""
       yaml_config = '''
       extensions: ["your-extension"]
       
       pipeline:
         nodes:
           - processor: YourProcessor
             parameters:
               strategy: "local"
               options:
                 max_iterations: 100
                 tolerance: 1e-6
       '''
       
       import yaml
       config = yaml.safe_load(yaml_config)
       
       pipeline = Pipeline.from_dict(config)
       result = pipeline.process(Payload(data=None, context=ContextType()))
       
       # Verify results
       result_value = result.context.get_value("processor.result")
       assert result_value is not None

Testing Complex Processors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For processors that perform complex operations (like optimization, model fitting, etc.), pipeline-based tests provide the most realistic validation:

.. code-block:: python

   def test_complex_processor_integration():
       """Test complex processor with full parameter resolution."""
       config = {
           "extensions": ["semantiva_optimize"],
           "pipeline": {
               "nodes": [
                   {
                       "processor": "OptimizerContextProcessor",
                       "parameters": {
                           "strategy": "local",
                           "x0": [0.5],
                           "bounds": [[-10, 10]],
                           "model": YourModel(),
                           "termination": {
                               "max_evals": 200,
                               "ftol_abs": 1e-12
                           }
                       }
                   }
               ]
           }
       }
       
       pipeline = Pipeline.from_dict(config)
       result = pipeline.process(Payload(data=None, context=ContextType()))
       
       # Check optimization results
       best = result.context.get_value("optimizer.best_candidate")
       assert "x" in best and "value" in best
       
       history = result.context.get_value("optimizer.history")
       assert len(history) > 0

Node-Based Testing (Limited Use)
---------------------------------

Node-based testing involves direct processor instantiation and should only be used when:

1. Pipeline testing is not feasible due to complex setup requirements
2. Testing very specific processor behaviors in isolation
3. Performance testing where pipeline overhead is problematic

.. warning::
   When using node-based testing, **never** directly instantiate ``_ContextObserver`` or other internal framework APIs. Use the proper node execution infrastructure.

Correct Node-Based Testing Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_processor_node_correctly():
       """Correct approach for node-based testing."""
       from semantiva.pipeline.node import Node
       from semantiva.pipeline.payload import Payload
       from semantiva.context_processors.context_types import ContextType
       
       # Create node properly
       node = Node(
           processor_name="YourProcessor",
           parameters={
               "param1": "value1",
               "param2": "value2"
           }
       )
       
       # Process with proper infrastructure
       initial_payload = Payload(data=test_data, context=ContextType())
       result_payload = node.process(initial_payload)
       
       # Check results in context
       result = result_payload.context.get_value("your.result.key")
       assert result == expected_value

Antipatterns to Avoid
---------------------

The following patterns should be avoided in tests:

Antipattern 1: Direct Observer Instantiation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ❌ DON'T DO THIS
   def test_processor_wrong():
       processor = YourProcessor()
       context = ContextType()
       observer = _ContextObserver(context)  # Internal API!
       
       processor.operate_context_observer(observer, parameters)
       
       # This creates confusion about where to check results
       result = observer.observer_context.get_value("key")  # ❌
       # vs
       result = context.get_value("key")  # ❌ Which one?

Antipattern 2: Testing Against Internal State
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ❌ DON'T DO THIS  
   def test_processor_internal_state():
       processor = YourProcessor()
       processor._internal_method()  # Testing private methods
       assert processor._internal_state == expected  # Testing private state

Antipattern 3: Mocking Framework Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ❌ DON'T DO THIS
   def test_with_excessive_mocking():
       with patch('semantiva.pipeline.node.Node'):
           with patch('semantiva.context_processors.observer._ContextObserver'):
               # Over-mocking breaks the framework contract
               test_logic()

