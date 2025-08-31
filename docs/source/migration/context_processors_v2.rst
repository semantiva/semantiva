Migrating ContextProcessors to v2
=================================

Checklist
---------
- Remove ``context`` param from ``_process_logic``.
- Replace returns with observer notifications.
- Declare keys: ``get_required_keys``, ``get_created_keys``, ``get_suppressed_keys``.
- Move any defaulting to signature defaults.

Before / After
--------------

.. code-block:: python
   :caption: BEFORE (legacy)

   class LegacyCP(ContextProcessor):
       def _process_logic(self, context, *, t: float = 0.0):
           context.set_value("foo", t)
           return context

.. code-block:: python
   :caption: AFTER (v2)

   class NewCP(ContextProcessor):
       @classmethod
       def get_created_keys(cls): return ["foo"]
       def _process_logic(self, *, t: float = 0.0) -> None:
           self._notify_context_update("foo", t)

Validation gotchas
------------------
- Writes must target ``get_created_keys``; otherwise ``KeyError``.
- Deletes must target ``get_suppressed_keys``; otherwise ``KeyError``.
- Parameter resolution precedence changed (node > context > defaults).
