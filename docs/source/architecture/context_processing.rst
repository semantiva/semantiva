Context Processing Architecture
===============================

Rationale
---------
* Stateless processors → reproducible + inspectable behavior.
* Observer mediates all writes/deletes → safe, validated mutations.
* Parameter resolution at runtime → config/context/defaults unified.

Key Classes
-----------
* ``semantiva.context_processors.context_processors.ContextProcessor`` — implements stateless ``_process_logic`` and notifiers.
* ``semantiva.context_processors.context_observer._ContextObserver`` — routes updates to the active context (single or collection).
* ``semantiva.context_processors.context_observer._ValidatingContextObserver`` — enforces allowed created/suppressed keys.
* Nodes wire observers in ``semantiva.pipeline.nodes.nodes``.

Lifecycle
---------
1. Node builds a :term:`GraphV1`, pulls :term:`node_uuid`.
2. Node resolves parameters (node config > context > defaults).
3. Node creates a ``_ValidatingContextObserver`` with:
   * ``context_keys`` ← ``processor.context_keys()`` or ``get_created_keys()``
   * ``suppressed_keys`` ← ``processor.get_suppressed_keys()``
4. Node calls ``processor.operate_context(context=context, context_observer=observer, **params)``.
5. Processor calls ``_notify_context_update/delete``; observer validates and writes.

Parameter Resolution
--------------------
Order: **node parameters > context > defaults**. Missing required params raise:
``KeyError: Unable to resolve parameter 'name' from context, node configuration, or defaults.``

Collections & ChainMap
----------------------
Observers support:
* ``ContextType`` — single context
* ``ContextCollectionType`` — collection, with optional index writes
* ``ChainMap`` — writes go to the local (first) mapping

Performance
-----------
All validation is O(1) on declared sets; no global scans. Tracing remains opt-in; see :doc:`../tracing`.
