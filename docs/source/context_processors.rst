Context Processors
==================

Overview
--------

A ContextProcessor is **stateless**: it implements ``_process_logic(**kwargs)`` and
never mutates context directly. All writes/deletes are **mediated** through the node’s
observer via ``_notify_context_update(key, value)`` and ``_notify_context_deletion(key)``.

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
