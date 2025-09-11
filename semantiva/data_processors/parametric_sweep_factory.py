# Copyright 2025 Semantiva authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import Any, Dict, Type, Optional, Union, Sequence, Literal
from dataclasses import dataclass
import itertools

import numpy as np

from semantiva.data_io.data_io import DataSource
from semantiva.data_processors.data_processors import DataOperation
from semantiva.data_types import NoDataType, DataCollectionType


@dataclass
class RangeSpec:
    """Specification for a numeric range variable.

    Args:
        lo: Lower bound of the range (inclusive).
        hi: Upper bound of the range.
        steps: Number of steps to generate in the range.
        scale: Scale type for range generation. 'linear' uses numpy.linspace,
               'log' uses numpy.logspace (base 10).
        endpoint: Whether to include the upper bound. When True, the sequence
                 includes both lo and hi. When False, hi is excluded.
    """

    lo: float
    hi: float
    steps: int
    scale: Literal["linear", "log"] = "linear"
    endpoint: bool = True

    def __post_init__(self):
        if self.steps <= 0:
            raise ValueError("steps must be positive")
        if self.scale not in ("linear", "log"):
            raise ValueError("scale must be 'linear' or 'log'")
        if self.scale == "log" and (self.lo <= 0 or self.hi <= 0):
            raise ValueError("log scale requires positive bounds")


@dataclass
class SequenceSpec:
    """Specification for an explicit sequence variable.

    Args:
        values: Sequence of values to use for this variable.
    """

    values: Sequence[Any]

    def __post_init__(self):
        if not self.values:
            raise ValueError("values must be non-empty")
        if isinstance(self.values, (str, bytes)):
            raise TypeError("values must be a non-string sequence")


class FromContext:
    """Sentinel specifying that a sequence should be read from the context."""

    def __init__(self, key: str) -> None:
        self.key = key

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"FromContext({self.key!r})"


# Type alias for variable specifications
VarSpec = Union[RangeSpec, SequenceSpec, FromContext]


__all__ = [
    "ParametricSweepFactory",
    "RangeSpec",
    "SequenceSpec",
    "FromContext",
    "VarSpec",
]


class ParametricSweepFactory:
    """Factory for creating parametric sweep data operations.

    The factory builds :class:`~semantiva.data_processors.data_processors.DataOperation`
    subclasses that generate data collections by iterating over one or more
    **independent variables**. Variables are specified using :class:`RangeSpec`,
    :class:`SequenceSpec`, or :class:`FromContext` for runtime-determined sequences.

    Range specifications support both linear and logarithmic scaling with configurable
    step counts and endpoint inclusion. Sequence specifications allow explicit values
    including non-numeric data like filenames. Context specifications enable dynamic
    parameter discovery at pipeline execution time.

    During execution each step constructs a parameter mapping from the current
    independent values, evaluates any ``parametric_expressions`` against that
    mapping, merges static parameters, and calls the provided ``DataSource``.
    The sequences of independent values are always published to the pipeline
    context using ``"{var}_values"`` keys so downstream processors can access them.

    Two sweep modes are supported: **product mode** (default) generates the Cartesian
    product of all variable values for comprehensive parameter exploration, while
    **zip mode** pairs variables element-wise for coordinated parameter sweeps.

    Examples
    --------
    **Product mode for hyperparameter exploration:**

    .. code-block:: python

        Sweep = ParametricSweepFactory.create(
            element_source=ModelSource,
            collection_output=ResultCollection,
            vars={
                "learning_rate": RangeSpec(0.001, 0.1, steps=3, scale='log'),
                "batch_size": SequenceSpec([16, 32, 64])
            },
            parametric_expressions={"model_name": "f'lr{learning_rate}_bs{batch_size}'"},
            mode="product"
        )

    **Zip mode for coordinated file processing:**

    .. code-block:: python

        Sweep = ParametricSweepFactory.create(
            element_source=FileProcessor,
            collection_output=ProcessedCollection,
            vars={
                "input_file": SequenceSpec(["data1.txt", "data2.txt"]),
                "scale": RangeSpec(0.5, 1.5, steps=2)
            },
            parametric_expressions={"output_file": "input_file.replace('.txt', '_scaled.txt')"},
            mode="zip"
        )
    """

    @staticmethod
    def create(
        element_source: Type[DataSource],
        collection_output: Type[DataCollectionType],
        vars: Dict[str, VarSpec],
        parametric_expressions: Dict[str, str],
        static_params: Optional[Dict[str, Any]] = None,
        include_independent: bool = False,
        mode: str = "product",
        broadcast: bool = False,
        name: Optional[str] = None,
    ) -> Type[DataOperation]:
        """Create a parametric sweep DataOperation class.

        Produces a DataOperation subclass that generates a collection of data elements
        by systematically varying parameters and calling the specified DataSource.
        Each generated element represents one point in the parameter space.

        Args:
            element_source: DataSource subclass used to generate individual data elements.
                           Called once per parameter combination with computed parameters.
            collection_output: DataCollectionType subclass for storing generated elements.
                              Must be compatible with element_source output type.
            vars: Mapping of variable names to their specifications. Each value must be
                 a RangeSpec for numeric ranges, SequenceSpec for explicit sequences,
                 or FromContext to fetch a sequence from the runtime context.
            parametric_expressions: Dictionary mapping parameter names to mathematical expressions.
                                   Expressions are evaluated with independent variables in scope.
                                   Example: {"frequency": "2 * time + 1", "phase": "amplitude / 10"}
            static_params: Fixed parameters passed to DataSource unchanged across all
                elements. Merged with computed dynamic parameters for each call.
            include_independent: When True the current values of the independent
                variables are forwarded directly to the DataSource in addition to
                any evaluated expressions.
            mode: Sweep mode determining how independent variables are combined.
                "product" (default): Variables are combined in Cartesian product fashion.
                Each value of each variable is paired with every value of every other
                variable. Results in N1 × N2 × ... × Nk elements.
                "zip": Variables are paired element-wise. All sequences must have
                compatible lengths. Results in N elements where N is determined by
                the longest sequence (with broadcast) or requires identical lengths.
            broadcast: Only used in zip mode. When True, shorter sequences are
                repeated to match the longest sequence length. When False (default),
                all sequences must have identical lengths.
            name: Optional class name for generated operation. Defaults to
                 "{element_source.__name__}ParametricSweep".

        Returns:
            DataOperation subclass configured for the specified parametric sweep.
            The class takes NoDataType input and produces collection_output type.

        Raises:
            TypeError: If element_source is not a DataSource subclass or
                collection_output is not a DataCollectionType subclass.
            ValueError: If vars is empty or mode is not supported.

        Examples:
        --------
        **Product Mode (Cartesian Product):**

        ```python
        # Full parameter exploration with ranges and sequences
        SweepClass = ParametricSweepFactory.create(
            element_source=ModelDataSource,
            collection_output=ResultCollection,
            vars={
                "learning_rate": RangeSpec(0.001, 0.1, steps=3, scale='log'),
                "batch_size": SequenceSpec([16, 32, 64]),
                "optimizer": SequenceSpec(["adam", "sgd"])
            },
            parametric_expressions={"experiment_id": "f'{optimizer}_lr{learning_rate}_bs{batch_size}'"},
            mode="product"
        )
        # Produces 18 elements (3 × 3 × 2)
        ```

        **Zip Mode (Element-wise Pairing):**

        ```python
        # Process corresponding files with matching parameters
        SweepClass = ParametricSweepFactory.create(
            element_source=ProcessorDataSource,
            collection_output=ProcessedCollection,
            vars={
                "input_file": SequenceSpec(["data1.txt", "data2.txt", "data3.txt"]),
                "scale_factor": RangeSpec(0.5, 1.5, steps=3),
                "method": SequenceSpec(["fast", "accurate", "balanced"])
            },
            parametric_expressions={"output_file": "input_file.replace('.txt', '_processed.txt')"},
            mode="zip"
        )
        # Produces 3 elements with corresponding parameters
        ```

        **Context Integration:**

        ```python
        # Runtime-determined sequences
        SweepClass = ParametricSweepFactory.create(
            element_source=AnalysisDataSource,
            collection_output=AnalysisCollection,
            vars={
                "data_files": FromContext("discovered_files"),
                "analysis_params": FromContext("parameter_sets")
            },
            parametric_expressions={"output_name": "f'analysis_{data_files}_{analysis_params}'"},
            mode="zip",  # Process each file with corresponding parameters
            broadcast=True  # Handle different sequence lengths
        )
        ```
        """

        if not issubclass(element_source, DataSource):
            raise TypeError("element_source must be a DataSource subclass")
        if not issubclass(collection_output, DataCollectionType):
            raise TypeError("collection_output must be a DataCollectionType subclass")
        if not vars:
            raise ValueError("vars must be non-empty")
        if mode not in ("zip", "product"):
            raise ValueError("mode must be 'zip' or 'product'")

        class_name = name or f"{element_source.__name__}ParametricSweep"

        class ParametricSweep(DataOperation):
            """Dynamically created parametric sweep operation.

            This operation generates a collection of data elements by iterating over
            variable specifications. Variables may be defined as numeric ranges,
            explicit sequences, or values pulled from the pipeline context at runtime.
            For each step the current independent values are combined with evaluated
            parametric_expressions and passed to the configured DataSource.

            Context Updates:
            - Injects "{variable}_values" sequences for each independent variable
            - Sequences contain the actual values used during generation
            - Available for downstream operations and analysis
            """

            _element_source = element_source
            _collection_output = collection_output
            _vars = vars
            _parametric_expressions = parametric_expressions
            _static_params = static_params or {}
            _include_independent = include_independent
            _mode = mode
            _broadcast = broadcast

            @classmethod
            def input_data_type(cls) -> Type[NoDataType]:
                """Return the input data type for this operation."""
                return NoDataType

            @classmethod
            def output_data_type(cls) -> Type[DataCollectionType]:
                """Return the output data type for this operation."""
                return cls._collection_output

            @classmethod
            def context_keys(cls):
                """Return context keys that will be created during sweep execution.

                Returns:
                    List of context key names in format "{variable}_values" for
                    each independent variable. These keys contain the parameter
                    sequences used during data generation.
                """
                return [f"{var}_values" for var in cls._vars]

            def _process_logic(
                self, data: NoDataType, *args, **kwargs
            ) -> DataCollectionType:
                """Execute the configured parametric sweep using VarSpec specifications."""

                sequences: Dict[str, Sequence[Any]] = {}

                # Process each variable specification
                for var, spec in self._vars.items():
                    if isinstance(spec, RangeSpec):
                        if spec.scale == "linear":
                            values = np.linspace(
                                spec.lo, spec.hi, spec.steps, endpoint=spec.endpoint
                            )
                        elif spec.scale == "log":
                            if spec.endpoint:
                                values = np.logspace(
                                    np.log10(spec.lo), np.log10(spec.hi), spec.steps
                                )
                            else:
                                # For log scale without endpoint, we need to adjust the upper bound
                                log_range = np.log10(spec.hi) - np.log10(spec.lo)
                                adjusted_hi = spec.lo * (
                                    10 ** (log_range * (spec.steps - 1) / spec.steps)
                                )
                                values = np.logspace(
                                    np.log10(spec.lo), np.log10(adjusted_hi), spec.steps
                                )
                        sequences[var] = list(values)

                    elif isinstance(spec, SequenceSpec):
                        sequences[var] = list(spec.values)

                    elif isinstance(spec, FromContext):
                        if not self.context_observer:
                            raise RuntimeError(
                                "FromContext was specified but no context_observer is bound"
                            )
                        value = self.context_observer.observer_context.get_value(
                            spec.key
                        )
                        if value is None:
                            raise ValueError(
                                f"Context key '{spec.key}' missing for variable '{var}'"
                            )
                        if isinstance(value, (str, bytes)) or not isinstance(
                            value, Sequence
                        ):
                            raise TypeError(
                                f"Context key '{spec.key}' must be a non-string sequence"
                            )
                        seq_list = list(value)
                        if not seq_list:
                            raise ValueError(
                                f"Context key '{spec.key}' must be a non-empty sequence"
                            )
                        sequences[var] = seq_list
                    else:
                        raise TypeError(
                            f"Invalid specification for variable '{var}': {type(spec)}"
                        )

                # Publish sequences to context
                for var, seq_values in sequences.items():
                    self._notify_context_update(f"{var}_values", seq_values)

                # Generate elements based on mode
                if self._mode == "zip":
                    return self._generate_zip_mode(sequences)
                elif self._mode == "product":
                    return self._generate_product_mode(sequences)
                else:
                    raise ValueError(f"Unsupported mode: {self._mode}")

            def _generate_zip_mode(
                self, sequences: Dict[str, Sequence[Any]]
            ) -> DataCollectionType:
                """Generate elements using zip mode (element-wise pairing)."""
                if not sequences:
                    return self._collection_output.from_list([])

                seq_lengths = [len(seq) for seq in sequences.values()]

                if self._broadcast:
                    # Broadcast mode: repeat shorter sequences to match the longest
                    max_length = max(seq_lengths)
                    expanded_sequences = {}
                    for var, seq in sequences.items():
                        if len(seq) == max_length:
                            expanded_sequences[var] = seq
                        else:
                            # Repeat sequence cyclically to match max_length
                            expanded_sequences[var] = [
                                seq[i % len(seq)] for i in range(max_length)
                            ]
                    sequences = expanded_sequences
                    step_count = max_length
                else:
                    # Strict mode: all sequences must have identical length
                    if len(set(seq_lengths)) != 1:
                        raise ValueError(
                            f"All variable sequences must have identical lengths in zip mode "
                            f"(found lengths: {seq_lengths}). Use broadcast=True to allow different lengths."
                        )
                    step_count = seq_lengths[0]

                # Prepare expression functions
                arg_list = ", ".join(self._vars.keys())
                funcs = {
                    name: eval(f"lambda {arg_list}: {expr}", {}, {})
                    for name, expr in self._parametric_expressions.items()
                }

                # Generate elements
                elements = []
                for i in range(step_count):
                    current = {var: sequences[var][i] for var in sequences}
                    dynamic = {name: func(**current) for name, func in funcs.items()}
                    params = {
                        **self._static_params,
                        **(current if self._include_independent else {}),
                        **dynamic,
                    }
                    elements.append(self._element_source.get_data(**params))
                return self._collection_output.from_list(elements)

            def _generate_product_mode(
                self, sequences: Dict[str, Sequence[Any]]
            ) -> DataCollectionType:
                """Generate elements using product mode (Cartesian product)."""
                if not sequences:
                    return self._collection_output.from_list([])

                # Prepare expression functions
                arg_list = ", ".join(self._vars.keys())
                funcs = {
                    name: eval(f"lambda {arg_list}: {expr}", {}, {})
                    for name, expr in self._parametric_expressions.items()
                }

                # Use consistent ordering for variables (sorted by key for reproducibility)
                var_names = sorted(sequences.keys())
                var_sequences = [sequences[var] for var in var_names]

                elements = []
                for combination in itertools.product(*var_sequences):
                    current = dict(zip(var_names, combination))
                    dynamic = {name: func(**current) for name, func in funcs.items()}
                    params = {
                        **self._static_params,
                        **(current if self._include_independent else {}),
                        **dynamic,
                    }
                    elements.append(self._element_source.get_data(**params))
                return self._collection_output.from_list(elements)

        ParametricSweep.__name__ = class_name
        ParametricSweep.__doc__ = (
            f"Parametric sweep data operation for {element_source.__name__} "
            f"producing {collection_output.__name__}."
        )

        return ParametricSweep
