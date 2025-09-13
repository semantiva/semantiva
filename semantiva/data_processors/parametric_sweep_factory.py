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

"""Parametric sweep factory.

This module provides a factory for creating "sweep" DataSource classes that
produce a typed collection by iterating over one or more independent variables
and invoking an underlying element DataSource for each combination (product)
or element-wise (zip) combination.

The factory implements:
- numeric ranges (RangeSpec), explicit sequences (SequenceSpec), and
    context-driven sequences (FromContext)
- safe expression evaluation for parametric expressions via
    :class:`semantiva.utils.safe_eval.ExpressionEvaluator` (tuples and simple
    type conversion functions are supported)
- automatic creation of context keys named ``{var}_values`` for downstream
    processors

This file is intentionally implementation-only: use the public
`ParametricSweepFactory.create` call documented below to construct sweep
sources.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import inspect
from typing import Any, Dict, Sequence, Type, Union, Literal, cast

import numpy as np

from semantiva.data_io.data_io import DataSource
from semantiva.data_types import DataCollectionType
from semantiva.utils.safe_eval import ExpressionEvaluator, ExpressionError


@dataclass
class RangeSpec:
    """Specification for a numeric range variable.

    Args:
        lo: Lower bound of the range.
        hi: Upper bound of the range.
        steps: Number of values to generate (must be positive).
        scale: "linear" (default) or "log" for logarithmic spacing.
        endpoint: Whether to include the upper bound in the generated values.
    """

    lo: float
    hi: float
    steps: int
    scale: Literal["linear", "log"] = "linear"
    endpoint: bool = True

    def __post_init__(self) -> None:
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
        values: Any non-empty, non-string sequence of values to be iterated.
    """

    values: Sequence[Any]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("values must be non-empty")
        if isinstance(self.values, (str, bytes)):
            raise TypeError("values must be a non-string sequence")


class FromContext:
    """Sentinel specifying that a sequence should be read from the pipeline
    context at runtime.

    Use this when the sweep values are produced earlier in the pipeline and
    stored in the context. The factory will expose the required context key
    via processor inspection and will create a ``{var}_values`` context entry
    containing the materialized sequence for downstream processors.

    Args:
        key: The context key name to read the sequence from.
    """

    def __init__(self, key: str) -> None:
        self.key = key

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"FromContext({self.key!r})"


VarSpec = Union[RangeSpec, SequenceSpec, FromContext]

__all__ = [
    "ParametricSweepFactory",
    "RangeSpec",
    "SequenceSpec",
    "FromContext",
    "VarSpec",
]


def _materialize_sequences(
    *,
    vars: Dict[str, VarSpec],
    params: Dict[str, Any],
) -> tuple[Dict[str, Sequence[Any]], Dict[str, Sequence[Any]]]:
    sequences: Dict[str, Sequence[Any]] = {}
    created: Dict[str, Sequence[Any]] = {}
    for var, spec in vars.items():
        if isinstance(spec, RangeSpec):
            if spec.scale == "linear":
                values = np.linspace(
                    spec.lo, spec.hi, spec.steps, endpoint=spec.endpoint
                )
            else:
                if spec.endpoint:
                    values = np.logspace(
                        np.log10(spec.lo), np.log10(spec.hi), spec.steps
                    )
                else:
                    log_range = np.log10(spec.hi) - np.log10(spec.lo)
                    adjusted_hi = spec.lo * (
                        10 ** (log_range * (spec.steps - 1) / spec.steps)
                    )
                    values = np.logspace(
                        np.log10(spec.lo), np.log10(adjusted_hi), spec.steps
                    )
            seq_list = list(values)
        elif isinstance(spec, SequenceSpec):
            seq_list = list(spec.values)
        elif isinstance(spec, FromContext):
            if spec.key not in params:
                raise ValueError(
                    f"Context key '{spec.key}' missing for variable '{var}'"
                )
            value = params[spec.key]
            if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
                raise TypeError(
                    f"Context key '{spec.key}' must be a non-string sequence"
                )
            seq_list = list(value)
            if not seq_list:
                raise ValueError(
                    f"Context key '{spec.key}' must be a non-empty sequence"
                )
        else:  # pragma: no cover - defensive
            raise TypeError(f"Invalid specification for variable '{var}'")
        sequences[var] = seq_list
        created[f"{var}_values"] = seq_list
    return sequences, created


def _iterate_sweep(
    sequences: Dict[str, Sequence[Any]],
    *,
    mode: Literal["product", "zip"],
    broadcast: bool,
):
    if not sequences:
        return []
    if mode == "zip":
        seq_lengths = [len(seq) for seq in sequences.values()]
        if broadcast:
            max_len = max(seq_lengths)
            expanded: Dict[str, Sequence[Any]] = {}
            for var, seq in sequences.items():
                if len(seq) == max_len:
                    expanded[var] = seq
                else:
                    expanded[var] = [seq[i % len(seq)] for i in range(max_len)]
            sequences = expanded
            step_count = max_len
        else:
            if len(set(seq_lengths)) != 1:
                raise ValueError(
                    "All variable sequences must have identical lengths in zip mode"
                )
            step_count = seq_lengths[0]
        for i in range(step_count):
            yield {var: sequences[var][i] for var in sequences}
    else:  # product
        var_names = sorted(sequences.keys())
        var_seqs = [sequences[v] for v in var_names]
        for combo in itertools.product(*var_seqs):
            yield dict(zip(var_names, combo))


def _validate_element_source_signature(
    *,
    element_source: Type[DataSource],
    vars: Dict[str, VarSpec],
    parametric_expressions: Dict[str, str] | None,
    static_params: Dict[str, Any] | None,
    include_independent: bool,
) -> None:
    """Validate planned parameters against the element source signature."""
    sig = inspect.signature(element_source._get_data)
    source_params = {n for n, p in sig.parameters.items() if n != "self"}
    independent_names = set(vars.keys())
    expr_out = set((parametric_expressions or {}).keys())
    static_names = set((static_params or {}).keys())
    forwarded = independent_names if include_independent else set()
    planned = expr_out | static_names | forwarded

    unknown = planned - source_params
    if unknown:
        raise TypeError(
            f"Parametric sweep will pass parameters not accepted by {element_source.__name__}: {sorted(unknown)}. "
            f"Allowed parameters: {sorted(source_params)}"
        )

    missing_required = {
        n
        for n, p in sig.parameters.items()
        if n != "self" and p.default is inspect._empty and n not in planned
    }
    if missing_required:
        raise TypeError(
            f"Element source {element_source.__name__} requires parameters not provided by sweep: {sorted(missing_required)}"
        )


def _compile_parametric_expressions(
    exprs: Dict[str, str], allowed_names: set[str], evaluator: ExpressionEvaluator
) -> Dict[str, Any]:
    compiled: Dict[str, Any] = {}
    for out_param, expr in exprs.items():
        try:
            compiled[out_param] = evaluator.compile(expr, allowed_names)
        except ExpressionError as exc:  # pragma: no cover - error path
            raise ValueError(
                f"Invalid parametric expression for '{out_param}': {exc}"
            ) from exc
    return compiled


class ParametricSweepFactory:
    """Factory for creating parametric sweep data sources."""

    @staticmethod
    def create(
        *,
        element: Type,
        element_kind: Literal[
            "DataSource", "DataOperation", "DataProbe"
        ] = "DataSource",
        collection_output: Type[DataCollectionType],
        vars: Dict[str, VarSpec],
        parametric_expressions: Dict[str, str] | None = None,
        static_params: Dict[str, Any] | None = None,
        include_independent: bool = False,
        mode: Literal["product", "zip"] = "product",
        broadcast: bool = False,
        name: str | None = None,
        expression_evaluator: ExpressionEvaluator | None = None,
    ) -> Type[DataSource]:
        if element_kind != "DataSource":
            raise NotImplementedError(
                "Sweep factory currently supports element_kind='DataSource' only. "
                "API is future-ready for DataOperation/DataProbe but not implemented in this epic."
            )
        element_source: Type[DataSource] = element  # type: ignore[assignment]
        if not issubclass(element_source, DataSource):
            raise TypeError("element must be a DataSource subclass")
        if not issubclass(collection_output, DataCollectionType):
            raise TypeError("collection_output must be a DataCollectionType subclass")
        if not vars:
            raise ValueError("vars must be non-empty")
        if mode not in {"product", "zip"}:
            raise ValueError("mode must be 'product' or 'zip'")

        evaluator = expression_evaluator or ExpressionEvaluator()

        _validate_element_source_signature(
            element_source=element_source,
            vars=vars,
            parametric_expressions=parametric_expressions,
            static_params=static_params,
            include_independent=include_independent,
        )

        compiled_exprs = _compile_parametric_expressions(
            parametric_expressions or {}, set(vars.keys()), evaluator
        )

        normalized_static: Dict[str, Any] = (
            {} if static_params is None else cast(Dict[str, Any], static_params)
        )

        processed_vars = vars

        class ParametricSweepSource(DataSource):
            _element_source = element_source
            _collection_output = collection_output
            _vars = processed_vars
            _parametric_expressions = parametric_expressions or {}
            _compiled_exprs = compiled_exprs
            _static_params: Dict[str, Any] = normalized_static
            _include_independent = include_independent
            _mode = mode
            _broadcast = broadcast

            @classmethod
            def output_data_type(cls) -> Type[DataCollectionType]:  # type: ignore[type-var]
                return cls._collection_output

            @classmethod
            def get_context_requirements(cls) -> list[str]:
                required = []
                for spec in cls._vars.values():
                    if isinstance(spec, FromContext):
                        required.append(spec.key)
                return required

            @classmethod
            def get_processing_parameter_names(cls) -> list[str]:
                return cls.get_context_requirements()

            @classmethod
            def get_created_keys(cls) -> list[str]:
                return [f"{var}_values" for var in cls._vars]

            @classmethod
            def _get_data(cls, **kwargs) -> DataCollectionType:  # type: ignore[type-var]
                ctx = kwargs.pop("context", None)
                sequences, created = _materialize_sequences(
                    vars=cls._vars,
                    params=kwargs,
                )
                if ctx is not None:
                    if hasattr(ctx, "set_value"):
                        for k, v in created.items():
                            ctx.set_value(k, v)
                    elif hasattr(ctx, "update"):
                        ctx.update(created)
                items = []
                for sweep_args in _iterate_sweep(
                    sequences, mode=cls._mode, broadcast=cls._broadcast
                ):
                    call_params = dict(cls._static_params)
                    if cls._include_independent:
                        call_params.update(sweep_args)
                    for out_param, fn in cls._compiled_exprs.items():
                        call_params[out_param] = fn(**sweep_args)
                    elem = cls._element_source.get_data(**call_params)
                    items.append(elem)
                return cls._collection_output.from_list(items)

        # Create proper signature for _get_data to expose FromContext parameters
        def create_get_data_with_signature():
            import inspect

            # Collect FromContext parameter names
            from_context_params = []
            for spec in processed_vars.values():
                if isinstance(spec, FromContext):
                    from_context_params.append(spec.key)

            if from_context_params:
                # Create signature with explicit FromContext parameters
                params = [
                    inspect.Parameter("cls", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                ]
                for param_name in from_context_params:
                    params.append(
                        inspect.Parameter(
                            param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD
                        )
                    )
                params.append(
                    inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD)
                )

                new_sig = inspect.Signature(params)
                ParametricSweepSource._get_data.__func__.__signature__ = new_sig

        # Create proper signature for _get_data to expose FromContext parameters

        create_get_data_with_signature()

        ParametricSweepSource.__name__ = (
            name or f"{element_source.__name__}ParametricSweep"
        )
        ParametricSweepSource.__doc__ = f"Parametric sweep data source for {element_source.__name__} producing {collection_output.__name__}."
        return ParametricSweepSource
