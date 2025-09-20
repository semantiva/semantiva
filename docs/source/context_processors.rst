Context Processors
==================

Overview
--------

A ContextProcessor is **stateless**: it implements ``_process_logic(**kwargs)`` and
never mutates context directly. All writes/deletes are **mediated** through the node's
observer via ``_notify_context_update(key, value)`` and ``_notify_context_deletion(key)``.

**Important**: All parameters must be explicitly declared in the ``_process_logic`` signature.
`**kwargs` is not allowed for reliable provenance tracking.

Context Observer Pattern
------------------------

ContextProcessors use an **observer pattern** for context updates:

* **Processors**: Call ``_notify_context_update()`` to request context changes
* **Observers**: Handle the actual context mutations and validation
* **Nodes**: Create and manage observers automatically

**For Users**: You should never instantiate ``_ContextObserver`` directly. The framework
handles this through pipeline nodes.

.. code-block:: python

   class MyContextProcessor(ContextProcessor):
       def _process_logic(self, *, input_value: float) -> None:
           # ✅ Correct: Use the notification method
           self._notify_context_update("result", input_value * 2)
           
           # ❌ Wrong: Never access context directly
           # context["result"] = input_value * 2

Observer Lifecycle
~~~~~~~~~~~~~~~~~~

1. **Node Creation**: Pipeline nodes create ``_ValidatingContextObserver`` with declared keys
2. **Validation Setup**: Observer configured with ``get_created_keys()`` and ``get_suppressed_keys()``
3. **Processor Execution**: Processor calls ``_notify_context_update()``
4. **Observer Validation**: Observer validates key is allowed and performs the update
5. **Context Updated**: Changes are written to the active context

Parameter Validation Examples
-----------------------------

Valid Parameter Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import List
   from semantiva.context_processors.context_processors import ContextProcessor

   class ValidContextProcessor(ContextProcessor):
       """Writes result based on input_value and threshold."""

       @classmethod
       def get_created_keys(cls) -> List[str]:
           return ["result"]
       
       def _process_logic(self, *, input_value: float, threshold: float = 0.5) -> None:
           # ✅ All parameters explicitly declared
           result = "high" if input_value > threshold else "low"
           self._notify_context_update("result", result)

Invalid Parameter Patterns (Rejected)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ❌ This will also raise ValueError
   class InvalidMixedProcessor(ContextProcessor):
       def _process_logic(self, *, param1: float, **kwargs):
           # Even mixed explicit + kwargs is rejected
           pass

.. code-block:: python

   from typing import List
   from semantiva.context_processors.context_processors import ContextProcessor

   class AdvancedProcessor(ContextProcessor):
       """Writes two output keys based on input_value and threshold."""

       @classmethod
       def get_created_keys(cls) -> List[str]:
           return ["result.status", "result.confidence"]

       @classmethod
       def get_suppressed_keys(cls) -> List[str]:
           return []  # nothing deleted here

       def _process_logic(self, *, input_value: float, threshold: float = 0.5) -> None:
           if input_value > threshold:
               self._notify_context_update("result.status", "high")
               self._notify_context_update("result.confidence", 0.9)
           else:
               self._notify_context_update("result.status", "low")
               self._notify_context_update("result.confidence", 0.3)

Where do required keys come from?
---------------------------------

Required inputs are determined at **node level** by the
:ref:`pipeline-yaml-parameters-precedence` policy:

1. Node ``parameters`` in YAML
2. Existing values in ``payload.context``
3. Python defaults in ``_process_logic`` signature

If a name cannot be resolved by any of the above, it is a **required context key** for the pipeline.

Validation & Safe Mutation
--------------------------

Context writes/deletes are validated by the node’s validating observer:

* Allowed writes = ``get_created_keys``
* Allowed deletes = ``get_suppressed_keys``

If a processor tries to update or delete an undeclared key, a ``KeyError`` is raised.

Typical errors
~~~~~~~~~~~~~~

.. code-block:: text

   RuntimeError: AdvancedProcessor attempted a context update without an active ContextObserver.

.. code-block:: text

   KeyError: Invalid context key 'invalid.key' for processor. Allowed keys: ['result.confidence', 'result.status']

.. code-block:: text

   KeyError: Invalid suppressed key 'temp' for processor. Allowed suppressed keys: ['old.key']

Factories: rename/delete
------------------------

Use factory resolvers in YAML for common context transforms (no Python class needed):

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: "rename:metrics.sharpness:features.sharpness"
       - processor: "delete:metrics.temp"

These map to dynamic ``ContextProcessor`` classes via the registry resolvers. They
also participate in validation:

* ``rename:a:b`` — requires ``a``, creates ``b``, suppresses ``a``.
* ``delete:k`` — suppresses ``k``.

Factories: stringbuild
----------------------

Compose deterministic strings from existing context values without writing a
custom processor:

.. code-block:: yaml

   pipeline:
     nodes:
       - processor: 'stringbuild:"exp_{subject}_{run}.png":filename'

Rules:

* Placeholders must be simple identifiers like ``{subject}`` or ``{run}``.
* Every placeholder is required at runtime; missing keys raise ``KeyError``.
* Format conversions or specs (e.g., ``{value!r}``, ``{value:.3f}``) are not supported.
* The destination key may already exist and will be overwritten, mirroring rename/delete behavior.

Testing Context Processors
---------------------------

**Recommended Approach**: Use pipeline nodes for testing, not direct processor instantiation.

.. code-block:: python

   import pytest
   from semantiva.pipeline.pipeline import Pipeline
   from semantiva.pipeline.payload import Payload
   from semantiva.context_processors.context_types import ContextType

   def test_my_context_processor():
       """Test using pipeline infrastructure (recommended)."""
       config = {
           "pipeline": {
               "nodes": [
                   {
                       "processor": "MyContextProcessor",
                       "parameters": {"input_value": 5.0}
                   }
               ]
           }
       }
       
       pipeline = Pipeline.from_dict(config)
       initial_payload = Payload(data=None, context=ContextType())
       result_payload = pipeline.process(initial_payload)
       
       # Check results in the final context
       assert result_payload.context.get_value("result") == 10.0

**Alternative for Unit Tests**: If you must test processors directly, use this pattern:

.. code-block:: python

   def test_context_processor_direct():
       """Direct testing (use sparingly)."""
       from semantiva.context_processors.context_observer import _ContextObserver
       
       processor = MyContextProcessor()
       context = ContextType()
       observer = _ContextObserver()
       
       # Execute processor
       processor.operate_context(
           context=context,
           context_observer=observer,
           input_value=5.0
       )
       
       # ⚠️ Important: Check observer's context, not original context
       result = observer.observer_context.get_value("result")
       assert result == 10.0

.. warning::
   
   **Do not instantiate** ``_ContextObserver`` in production code or regular tests.
   Context observers are **framework internals** managed by pipeline nodes.
   
   Direct observer usage should be limited to:
   
   * Extension development and testing
   * Framework debugging
   * Advanced integration scenarios
   
   For most testing needs, use pipeline-based tests which provide better integration
   coverage and follow the intended usage patterns.

Autodoc
-------

.. automodule:: semantiva.context_processors.context_processors
   :members:
   :undoc-members:

.. automodule:: semantiva.context_processors.context_types
   :members:
   :undoc-members:

.. automodule:: semantiva.context_processors.factory
   :members:
   :undoc-members:
