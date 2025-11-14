Data collections
================

Data collections represent ordered sequences of data objects of the same base
``BaseDataType``. They let pipelines express "many items of the same kind"
without turning every element into a separate run.

What is a data collection?
---------------------------

A data collection is a container data type whose elements all share the same
base type. Examples include sequences of images, batches of measurement
records, or lists of scalar values.

Collections behave like any other data type:

- they have a well-defined element type,
- they can be produced by sources or operations, and
- they can be consumed by downstream processors that expect a collection.

Data processors for collections can be implemented directly for the collection
type, just as for any other data type. Slicers and parameter sweeps are
**optional automation tools** that simplify common patterns.

Slicers
-------

Slicer processors automate element-wise traversal of collections. Given a
processor built for the base element type, the slicer factory lifts it to
operate on the entire collection by applying the processor to each element in
sequence.

For data operations, the slicer:

- consumes a collection as input,
- applies the wrapped operation to every element in order, and
- returns a new collection of the same collection type with the processed
  elements.

For probes, the slicer:

- consumes a collection as input,
- runs the wrapped probe on every element, and
- returns a list of probe results.

The slicer preserves collection structure and ordering; it does not select
arbitrary subsets or re-order elements. This automation also ensures that the
element-wise pattern is visible in trace records and pipeline inspection
output.

Derive sweeps and collections
------------------------------

The ``derive.parameter_sweep`` preprocessor automates the creation of
processors that invoke a base processor multiple times with varied parameters,
collecting the outputs into a data collection or list.

Given:

- a processor (data source, data operation, or data probe), and
- a set of variables and expressions that define parameter grids,

parameter sweeps:

- evaluate parameter expressions over the variable grid,
- invoke the underlying processor repeatedly on the same input (for
  operations/probes) or to produce a sequence of outputs (for sources), and
- collect the results into a typed data collection or a list of probe results.

Like slicers, sweeps bring structure to trace records and inspection by
exposing the parameter grid and the generated sequence.

In summary:

- **Slicers** automate element-wise traversal of an existing collection using
  a processor designed for the base element type.
- **Sweeps** automate parameter-space traversal, building a collection by
  repeatedly invoking a processor with different parameter values.
- Both are optional conveniences; collection processors can also be
  implemented directly.

See :doc:`collection_modifiers` for detailed mechanics of slicers and sweeps,
and :doc:`data_types` for the collection data type contracts available in
Semantiva.
