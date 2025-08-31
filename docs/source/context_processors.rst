Context Processors
==================

Observer Pattern & Lifecycle
----------------------------

``ContextProcessor`` now uses a stateless, observer-mediated pattern. Processors
declare parameters in ``_process_logic`` and **never** mutate context directly;
all writes/deletes go through the active observer.

.. code-block:: python

   from typing import List
   from semantiva.context_processors.context_processors import ContextProcessor

   class AdvancedProcessor(ContextProcessor):
       """Write a couple of keys based on runtime parameters."""

       @classmethod
       def get_created_keys(cls) -> List[str]:
           return ["result.status", "result.confidence"]

       @classmethod
       def get_required_keys(cls) -> List[str]:
           # Required keys must exist in context (or be provided via params)
           return ["input_value"]

       def _process_logic(self, *, input_value: float, threshold: float = 0.5) -> None:
           if input_value > threshold:
               self._notify_context_update("result.status", "high")
               self._notify_context_update("result.confidence", 0.9)
           else:
               self._notify_context_update("result.status", "low")
               self._notify_context_update("result.confidence", 0.3)

**Runtime parameter resolution**: Parameters are resolved by the node as:
``node parameters > context values > default in signature``. See
:ref:`pipeline-yaml-parameters-precedence` for details.

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

Legacy pattern (deprecated)
---------------------------

Legacy processors that returned a modified context are supported but deprecated.

.. code-block:: python

   # OLD (deprecated)
   def _process_logic(self, context, threshold: float = 0.5):
       context.set_value("result", threshold > 0.5)
       return context

   # NEW (recommended)
   def _process_logic(self, *, threshold: float = 0.5) -> None:
       self._notify_context_update("result", threshold > 0.5)

``operate_context`` injects a validating observer and calls your ``_process_logic``;
the method must be **side-effect free** except via ``_notify_*``.

.. seealso::

   :doc:`architecture/context_processing` — deep dive into the architecture.

Migrating from legacy
---------------------

See :doc:`migration/context_processors_v2`.

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
