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

Observer Pattern Details
------------------------

The context observer pattern ensures safe, validated context mutations:

**Why Observer Pattern?**

* **Validation**: All context updates are checked against declared keys
* **Abstraction**: Processors don't need to know about context implementation details  
* **Flexibility**: Same processor works with single contexts, collections, or ChainMaps
* **Debugging**: All mutations are logged and traceable

**Observer Types**

* ``_ContextObserver`` — base implementation for context routing
* ``_ValidatingContextObserver`` — adds key validation against processor declarations
* Framework automatically chooses the appropriate observer based on processor metadata

**Internal API Warning**

``_ContextObserver`` classes are **framework internals**. Users should never:

* Instantiate observers directly
* Pass observers to processors manually  
* Access observer internals in application code

Observers are managed automatically by pipeline nodes. Direct usage should be
limited to framework development and extension testing.

Lifecycle
---------
1. Node builds a :term:`GraphV1`, pulls :term:`node_uuid`.
2. Node resolves parameters (node config > context > defaults).
3. Node creates a ``_ValidatingContextObserver`` with:
   * ``context_keys`` ← ``processor.context_keys()`` or ``get_created_keys()``
   * ``suppressed_keys`` ← ``processor.get_suppressed_keys()``
4. Node calls ``processor.operate_context(context=context, context_observer=observer, **params)``.
5. Processor calls ``_notify_context_update/delete``; observer validates and writes.
6. Observer updates the **active context** (the original context passed to the node).

.. note::
   
   **Testing Implication**: In tests using observers directly, check 
   ``observer.observer_context.get_value(key)`` not ``original_context.get_value(key)``.
   The observer maintains its own context copy for validation purposes.

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
