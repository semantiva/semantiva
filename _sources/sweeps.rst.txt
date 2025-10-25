Sweeps in YAML
==============

Objective
---------
This page documents the Parametric Sweep feature. The objective is to show
how to declare and run parameter sweeps that produce typed collections by
iterating over independent variables, how to write safe parametric
expressions that compute parameters for the element DataSource, and how to
use context values as inputs to a sweep.

Overview
--------
A **sweep is a DataSource** that constructs a collection (for example,
an image stack or a list of numeric values) by repeatedly invoking an
underlying element DataSource with different parameters. Sweeps help you
generate systematic variations (grids, series, or element-wise combinations)
without writing bespoke code.

Key concepts and parameters
---------------------------

- ``vars`` (required): A mapping of independent variable names to one of the
  variable specification types documented below. Each variable becomes an
  input to parametric expressions and (optionally) is forwarded to the
  element DataSource as an independent parameter.
- ``parametric_expressions`` (optional but common): A mapping from element
  parameter names to small expressions (strings). Each expression is
  evaluated for every sweep step and its result is passed to the element
  DataSource under the parameter name. Expressions use a safe AST-based
  evaluator (see "Notes on expressions" below). Example:

  parametric_expressions:
    value: "50 + 20 * t"

  This will evaluate ``50 + 20 * t`` for each value of ``t`` and set the
  element parameter ``value`` accordingly.
- ``static_params`` (optional): A mapping of parameters with fixed values
  passed unchanged to every element invocation.
- ``include_independent`` (optional boolean): When true, the independent
  variables from ``vars`` will be forwarded to the element DataSource as
  parameters (in addition to any parametric expression outputs).
- ``mode``: ``combinatorial`` (default) computes the Cartesian product of variable
  sequences; ``by_position`` pairs values element-wise (sequences must match lengths
  unless ``broadcast`` is true).
- ``broadcast`` (boolean, only for ``by_position`` mode): If true, shorter
  sequences are repeated to match the longest sequence length.

Variable specification types
----------------------------

- ``RangeSpec`` (YAML shorthand): Numeric range generation.

  YAML form: ``t: { lo: 0.0, hi: 1.0, steps: 5 }``

  Produces a numeric sequence of ``steps`` values between ``lo`` and ``hi``.
  Options: ``scale``: ``linear`` or ``log``; ``endpoint`` includes upper
  bound if true.

- ``SequenceSpec`` (YAML shorthand): Explicit sequence.

  YAML form: ``file: ["a.csv", "b.csv"]``

  Use when you have an explicit list of values.

- ``FromContext`` (YAML shorthand): Read a sequence from pipeline context.

  YAML form: ``sha: { from_context: commit_shas }``

  Use when an earlier processor placed a sequence into the pipeline context.
  The factory will validate the context entry is a non-empty, non-string
  sequence at runtime and expose the required context key to the inspection
  system.

Modes
-----

- ``combinatorial``: Cartesian product of sequences. If you have ``t=[a,b]`` and
  ``p=[1,2]`` you'll get four combinations: ``(a,1),(a,2),(b,1),(b,2)``.
- ``by_position``: Element-wise pairing. With ``by_position`` and ``broadcast=false`` the
  sequences must have equal length, and each step uses the corresponding
  elements. With ``broadcast=true`` shorter sequences are repeated.

Basic example
-------------

.. code-block:: yaml

  pipeline:
    nodes:
      - processor: "sweep:FloatValueDataSource:FloatDataCollection"
        parameters:
          vars:
            t: {lo: 0.0, hi: 1.0, steps: 5}
          parametric_expressions:
            value: "t * 2"
          include_independent: true

Explanation
-----------
With ``steps: 5`` the range ``t`` becomes the sequence ``[0.0, 0.25, 0.5,
0.75, 1.0]`` (linear spacing). The expression ``"t * 2"`` is evaluated for
each ``t`` producing ``[0.0, 0.5, 1.0, 1.5, 2.0]`` which are passed as the
``value`` parameter to the element DataSource. If ``include_independent`` is
true, the element will also receive ``t`` as a parameter along with ``value``.

From context & by_position mode
-------------------------------

.. code-block:: yaml

  pipeline:
    nodes:
      - processor: "sweep:AnalysisDataSource:AnalysisCollection"
        parameters:
          vars:
            file: {from_context: discovered_files}
            p:    {from_context: parameter_sets}
          parametric_expressions:
            name: "f'{file}_{p}'"
          mode: "by_position"
          broadcast: true

Explanation
-----------
Suppose the pipeline context contains ``discovered_files: ["a.tif", "b.tif"]``
and ``parameter_sets: ["A", "B", "C"]``. With ``mode: by_position`` and
``broadcast: true`` the shorter sequence (``discovered_files``) is repeated
to match the longer sequence, producing steps:

- step 0: file="a.tif", p="A" -> name="a.tif_A"
- step 1: file="b.tif", p="B" -> name="b.tif_B"
- step 2: file="a.tif", p="C" -> name="a.tif_C"

Each ``name`` is produced by evaluating the parametric expression
``f'{file}_{p}'`` for that step and passed to the element DataSource.

Inspection
----------
- Sweep sources **require** any ``FromContext`` keys; they appear in ``semantiva inspect``.
- Sweep sources **create** ``{var}_values`` context keys for downstream processors.

API reference (short)
---------------------

The factory exposes three small helper types you may use in YAML or the
programmatic API:

- ``RangeSpec(lo, hi, steps, scale='linear', endpoint=True)`` - produce a numeric
  range.
- ``SequenceSpec([...])`` - provide an explicit sequence of values.
- ``FromContext('key')`` - read a sequence from the pipeline context.

When using the programmatic API, call::

    ParametricSweepFactory.create(
        element=MyElementDataSource,
        collection_output=MyCollectionType,
        vars={ 't': RangeSpec(0,1,steps=5), 'file': SequenceSpec([...]) },
        parametric_expressions={ 'x': '50 + 20 * t', 'name': "'img_' + str(t)" },
        mode='combinatorial'|'by_position',
        include_independent=True|False,
    )

Notes on expressions
--------------------

- Expressions are parsed using a safe AST-based evaluator. This means:
    - No arbitrary ``eval`` or execution of imports.
    - Only simple function calls are allowed (``abs``, ``min``, ``max``, ``round``, and
      the type conversions ``float/int/str/bool``).
    - Tuples are supported which makes multi-valued parameters possible,
      e.g. ``"(50 + 20 * t, 20)"`` returns a 2-tuple for a multi-valued
      parameter.
    - Unknown variables or disallowed syntax raise clear errors at compile time.

Good practices
--------------

- Prefer explicit ``SequenceSpec`` or ``RangeSpec`` in YAML for readability.
- Use ``FromContext`` when sweep values are produced earlier in the same
  pipeline. The inspection output will list these required context keys.
- Use ``mode: by_position`` when you want element-wise pairing. If sequences have
  differing lengths and you still want element-wise operation, set
  ``broadcast: true`` to repeat shorter sequences.

Examples
--------

Tuple output (multi-valued parameter):

.. code-block:: yaml

  pipeline:
    nodes:
      - processor: "sweep:TwoDGaussianSingleChannelImageGenerator:SingleChannelImageStack"
        parameters:
          vars:
            t: {lo: -1, hi: 2, steps: 3}
          parametric_expressions:
            x_0: "50 + 5 * t"
            y_0: "50 + 5 * t + 5 * t ** 2"
            std_dev: "(50 + 20 * t, 20)"  # tuple -> (std_dev_x, std_dev_y)
            amplitude: "100"
            angle: "60 + 5 * t"

Explanation
-----------
The expression ``"(50 + 20 * t, 20)"`` evaluates to a tuple for each
``t``. For example, if ``t`` takes values ``[-1, 0, 1]`` then
``std_dev`` expands to the tuples ``[(30,20), (50,20), (70,20)]``. The
element DataSource must accept whatever parameter names you use (here the
factory will forward the evaluated ``std_dev`` value under that parameter
name). If your element understands separate ``std_dev_x`` and ``std_dev_y``
you can either emit those as separate expressions or unpack the tuple in the
element implementation.

FromContext example with type conversion in expressions:

.. code-block:: yaml

  pipeline:
    nodes:
      - processor: "sweep:FloatValueDataSource:FloatDataCollection"
        parameters:
          vars:
            input_value: { from_context: discovered_values }
          parametric_expressions:
            value: "float(input_value)"

Explanation
-----------
If the context key ``discovered_values`` contains strings like
``["1.5", "2.75"]``, the expression ``"float(input_value)"`` converts
each string to a floating point value resulting in ``[1.5, 2.75]`` which are
then passed to the element DataSource as the ``value`` parameter.

Expressions
-----------
- Expressions use a **safe evaluator** (no ``eval``).
- Allowed: declared variable names, ops (+, -, *, /, **), tuples, and functions: ``abs``, ``min``, ``max``, ``round``, ``float``, ``int``, ``str``, ``bool``.
- Clear errors for unknown variables or disallowed syntax.
- Tuple expressions like ``"(x + 1, y * 2)"`` are supported for multi-value parameters.
- Type conversion functions like ``"float(input_value)"`` are supported for data type conversion.
