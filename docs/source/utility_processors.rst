==================
Utility Components
==================

Semantiva provides two lightweight **utility components** designed to improve control 
and observability within pipelines: ``DataDump`` and ``CopyDataProbe``. Both operate 
entirely within normal Semantiva data-flow semantics and can be inserted anywhere in 
a pipeline without side effects on orchestration or context consistency.

Overview
========

Utility components are general-purpose processors that:

- Accept ``BaseDataType`` as input (universal compatibility)
- Operate on data and context channels independently
- Provide explicit control over data propagation and observation
- Are registered in the core framework (no extension required)

.. list-table:: Summary Table
   :header-rows: 1
   :widths: 15 15 20 15 20 15

   * - Utility
     - Type
     - Input → Output
     - Effect on Data
     - Effect on Context
     - Typical Use
   * - **DataDump**
     - DataOperation
     - BaseDataType → NoDataType
     - Discards data
     - Forwards unchanged
     - Restart data flow; insert new source
   * - **CopyDataProbe**
     - DataProbe
     - BaseDataType → BaseDataType
     - Forwards data
     - Identity (no changes)
     - Save intermediate values, debugging

DataDump — Explicit Data Channel Terminator
============================================

.. autoclass:: semantiva.data_processors.DataDump
   :members:
   :show-inheritance:

Purpose
-------

``DataDump`` is a universal "data dumper" operation that **stops data propagation** 
in the pipeline while **preserving the context**. It converts any ``BaseDataType`` 
input into ``NoDataType``, effectively signaling that downstream nodes should not 
expect data from previous stages.

This component is useful when you want to:

- **Reset** the data stream mid-pipeline before injecting a new ``DataSource``
- **Discard** intermediary data for performance or privacy reasons
- **Isolate** context continuity from data continuity

Behavior
--------

.. list-table::
   :widths: 30 70

   * - **Component type**
     - ``DataOperation``
   * - **Input data type**
     - ``BaseDataType`` (accepts any subclass)
   * - **Output data type**
     - ``NoDataType``
   * - **Effect**
     - Drops incoming data, forwards context unchanged

Value
-----

- Enables **mid-pipeline re-seeding** of data (insert sources anywhere)
- Prevents accidental reuse of heavy or sensitive data objects
- Enhances modularity — context can continue while data resets cleanly

CopyDataProbe — Pass-Through Inspection
========================================

.. autoclass:: semantiva.data_processors.CopyDataProbe
   :members:
   :show-inheritance:

Purpose
-------

``CopyDataProbe`` allows you to **inspect data without modifying the data stream**. 
It acts as a transparent "tap" or "mirror": data flows through unchanged, making it 
ideal for debugging, logging, or verification points.

Typical uses include:

- **Debugging** during development (inspect intermediate states)
- **Logging** or analysis without affecting pipeline behavior
- **Verification** that data passes through correctly
- **Custom probes** via subclassing for metrics or monitoring

Behavior
--------

.. list-table::
   :widths: 30 70

   * - **Component type**
     - ``DataProbe``
   * - **Input data type**
     - ``BaseDataType`` (accepts any subclass)
   * - **Output data type**
     - Same as input (identity function)
   * - **Effect**
     - Returns input unchanged (preserves object identity)

Value
-----

- Offers a **non-intrusive way** to observe intermediate values
- Enables **verification points** without breaking data flow
- Ideal for **analysis**, **visualization**, or **debugging** pipelines

See Also
========

- :doc:`data_operations` and :doc:`data_probes` — Base classes for data processors
- :doc:`data_types` — Data type system overview
- :doc:`introspection_validation` — Type compatibility rules
- :doc:`creating_components` — Creating custom processors
- :doc:`pipeline` — Pipeline architecture and data flow
