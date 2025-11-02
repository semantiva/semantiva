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

"""Factory for creating parametric sweep processors.

This module implements the ``derive.parameter_sweep`` preprocessor, which generates
specialized processor classes that evaluate parameters across variable ranges.

**Parameter Resolution:**

- Expressions evaluate **parameters** using **variables** as inputs
- Expression parameter names must match the target processor's argument names
- Parameters not computed by expressions remain in the wrapper's signature for
  pipeline-level resolution
- Parameter precedence: computed values > node parameters > processor defaults

**Processor Types:**

- **DataSource**: Requires ``collection`` output type; produces a collection of results
- **DataOperation**: Requires ``collection`` output type; processes input data with
  swept parameters and produces a collection
- **DataProbe**: Forbids ``collection``; returns a list of probe results

**Validation:**

- Unknown parameter names in expressions raise ``TypeError``
- Missing required ``collection`` for DataSource/DataOperation raises ``TypeError``
- Invalid ``collection`` specification for DataProbe raises ``TypeError``
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import inspect
from typing import Any, Dict, Sequence, Type, Union, Literal, Set, List

import numpy as np

from semantiva.data_io.data_io import DataSource
from semantiva.data_types import DataCollectionType
from semantiva.data_processors.data_processors import DataOperation, DataProbe
from semantiva.utils.safe_eval import ExpressionEvaluator, ExpressionError
from semantiva.metadata import normalize_expression_sig_v1, variable_domain_signature


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
    mode: Literal["combinatorial", "by_position"],
    broadcast: bool,
):
    if not sequences:
        return []
    if mode == "by_position":
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
                    "All variable sequences must have identical lengths in by_position mode"
                )
            step_count = seq_lengths[0]
        for i in range(step_count):
            yield {var: sequences[var][i] for var in sequences}
    else:  # combinatorial
        var_names = sorted(sequences.keys())
        var_seqs = [sequences[v] for v in var_names]
        for combo in itertools.product(*var_seqs):
            yield dict(zip(var_names, combo))


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


def _validate_mode(mode: str) -> None:
    if mode not in {"combinatorial", "by_position"}:
        raise ValueError("mode must be 'combinatorial' or 'by_position'")


def _publish_created_context(
    created: Dict[str, Sequence[Any]], context: Any | None
) -> None:
    if context is None:
        return
    if hasattr(context, "set_value"):
        for key, value in created.items():
            context.set_value(key, value)
    elif hasattr(context, "update"):
        context.update(created)


def _allowed_parameter_names(
    element: Type[Any],
    element_kind: Literal["DataSource", "DataOperation", "DataProbe"],
) -> tuple[List[inspect.Parameter], Set[str]]:
    if element_kind == "DataSource":
        signature = inspect.signature(element._get_data)
        excluded = {"cls"}
    else:
        signature = inspect.signature(element._process_logic)
        excluded = {"self", "data"}

    parameters: List[inspect.Parameter] = []
    for param in signature.parameters.values():
        if param.name in excluded:
            continue
        if param.kind not in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            continue
        parameters.append(param)

    names = {param.name for param in parameters}
    return parameters, names


def _build_signature(
    *,
    is_classmethod: bool,
    context_keys: List[str],
    required_parameters: List[str],
    optional_parameters: Dict[str, Any],
) -> inspect.Signature:
    params: List[inspect.Parameter] = []
    first = "cls" if is_classmethod else "self"
    params.append(inspect.Parameter(first, inspect.Parameter.POSITIONAL_OR_KEYWORD))

    for key in context_keys:
        params.append(inspect.Parameter(key, inspect.Parameter.POSITIONAL_OR_KEYWORD))

    for name in required_parameters:
        params.append(inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD))

    for name, default in optional_parameters.items():
        params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
            )
        )

    params.append(inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD))
    return inspect.Signature(params)


def _merge_call_parameters(
    *,
    base_kwargs: Dict[str, Any],
    expression_outputs: Dict[str, Any],
) -> Dict[str, Any]:
    merged = dict(base_kwargs)
    merged.update(expression_outputs)
    return merged


class ParametricSweepFactory:
    """Factory for creating sweep processors across DataSource, DataOperation, and DataProbe."""

    @staticmethod
    def create(
        *,
        element: Type[Any],
        element_kind: Literal["DataSource", "DataOperation", "DataProbe"],
        collection_output: Type[DataCollectionType] | None,
        vars: Dict[str, VarSpec],
        parametric_expressions: Dict[str, str] | None = None,
        mode: Literal["combinatorial", "by_position"] = "combinatorial",
        broadcast: bool = False,
        name: str | None = None,
        expression_evaluator: ExpressionEvaluator | None = None,
    ) -> Type[Any]:
        if not vars:
            raise ValueError("vars must be non-empty")
        _validate_mode(mode)

        if element_kind == "DataSource":
            if not issubclass(element, DataSource):
                raise TypeError("element must be a DataSource subclass")
            if collection_output is None or not issubclass(
                collection_output, DataCollectionType
            ):
                raise TypeError(
                    "collection_output must be provided and be a DataCollectionType subclass"
                )
        elif element_kind == "DataOperation":
            if not issubclass(element, DataOperation):
                raise TypeError("element must be a DataOperation subclass")
            if collection_output is None or not issubclass(
                collection_output, DataCollectionType
            ):
                raise TypeError(
                    "DataOperation sweeps require a DataCollectionType collection_output"
                )
        elif element_kind == "DataProbe":
            if not issubclass(element, DataProbe):
                raise TypeError("element must be a DataProbe subclass")
            if collection_output is not None:
                raise TypeError("DataProbe sweeps must not provide a collection_output")
        else:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported element_kind '{element_kind}'")

        evaluator = expression_evaluator or ExpressionEvaluator()
        compiled_exprs = _compile_parametric_expressions(
            parametric_expressions or {}, set(vars.keys()), evaluator
        )
        expr_src = dict(parametric_expressions or {})

        parameters, allowed_names = _allowed_parameter_names(element, element_kind)

        unknown_expr = set((parametric_expressions or {}).keys()) - allowed_names
        if unknown_expr:
            raise TypeError(
                f"Parametric expressions target unknown parameters for {element.__name__}: {sorted(unknown_expr)}"
            )

        bound_names = set((parametric_expressions or {}).keys())

        required_external: List[str] = []
        optional_external: Dict[str, Any] = {}
        for param in parameters:
            if param.name in bound_names:
                continue
            if param.default is inspect._empty:
                required_external.append(param.name)
            else:
                optional_external[param.name] = param.default

        from_context_keys = [
            spec.key for spec in vars.values() if isinstance(spec, FromContext)
        ]

        external_param_names: List[str] = (
            list(from_context_keys)
            + list(required_external)
            + list(optional_external.keys())
        )

        base_kwargs_filter = set(required_external) | set(optional_external.keys())

        def _preprocessor_metadata(cls: Any) -> dict[str, Any]:
            element_ref = f"{cls._element.__module__}.{cls._element.__qualname__}"
            # Sanitized metadata: only include "sig", not "expr"
            param_expressions = {
                name: {"sig": normalize_expression_sig_v1(src)}
                for name, src in getattr(cls, "_expr_src", {}).items()
            }
            variables_meta = {
                name: variable_domain_signature(spec)
                for name, spec in getattr(cls, "_vars", {}).items()
            }
            collection = getattr(cls, "_collection_output", None)
            collection_ref = (
                f"{collection.__module__}.{collection.__qualname__}"
                if collection is not None
                else None
            )
            deps = {
                "required_external_parameters": list(
                    getattr(cls, "_required_external", ())
                ),
                "context_keys": list(getattr(cls, "_from_context_keys", ())),
            }
            return {
                "type": "derive.parameter_sweep",
                "version": 1,
                "element_ref": element_ref,
                "param_expressions": param_expressions,
                "variables": variables_meta,
                "mode": getattr(cls, "_mode", "combinatorial"),
                "broadcast": bool(getattr(cls, "_broadcast", False)),
                "collection": collection_ref,
                "dependencies": deps,
            }

        if element_kind == "DataSource":
            # At this point collection_output is guaranteed to be non-None for DataSource
            assert collection_output is not None

            class ParametricSweepSource(DataSource):
                _element = element
                _collection_output: Type[DataCollectionType] = collection_output  # type: ignore[assignment]
                _vars = vars
                _compiled_exprs = compiled_exprs
                _expr_src = expr_src
                _mode = mode
                _broadcast = broadcast
                _allowed_names = allowed_names
                _required_external = tuple(required_external)
                _optional_external = optional_external
                _from_context_keys = tuple(from_context_keys)
                _external_param_names = tuple(external_param_names)

                @classmethod
                def output_data_type(cls) -> Type[DataCollectionType]:  # type: ignore[type-var]
                    return cls._collection_output

                @classmethod
                def get_context_requirements(cls) -> list[str]:
                    return list(cls._from_context_keys)

                @classmethod
                def get_processing_parameter_names(cls) -> list[str]:
                    return list(cls._external_param_names)

                @classmethod
                def get_required_external_parameters(cls) -> list[str]:
                    return list(cls._from_context_keys) + list(cls._required_external)

                @classmethod
                def get_created_keys(cls) -> list[str]:
                    return [f"{var}_values" for var in cls._vars]

                @classmethod
                def _get_data(cls, **kwargs) -> DataCollectionType:  # type: ignore[type-var]
                    context = kwargs.pop("context", None)
                    sequences, created = _materialize_sequences(
                        vars=cls._vars,
                        params=kwargs,
                    )

                    for key in cls._from_context_keys:
                        kwargs.pop(key, None)

                    base_kwargs = {
                        name: kwargs[name]
                        for name in base_kwargs_filter
                        if name in kwargs
                    }

                    items = []
                    for sweep_args in _iterate_sweep(
                        sequences, mode=cls._mode, broadcast=cls._broadcast
                    ):
                        expr_outputs = {
                            out_param: fn(**sweep_args)
                            for out_param, fn in cls._compiled_exprs.items()
                        }
                        call_params = _merge_call_parameters(
                            base_kwargs=base_kwargs,
                            expression_outputs=expr_outputs,
                        )
                        call_params = {
                            key: value
                            for key, value in call_params.items()
                            if key in cls._allowed_names
                        }
                        items.append(cls._element.get_data(**call_params))

                    _publish_created_context(created, context)
                    return cls._collection_output.from_list(items)

                @classmethod
                def _define_metadata(cls) -> dict:
                    meta = dict(super()._define_metadata())
                    meta["preprocessor"] = _preprocessor_metadata(cls)
                    meta.setdefault("component_type", "DataSource")
                    return meta

            signature = _build_signature(
                is_classmethod=True,
                context_keys=list(from_context_keys),
                required_parameters=list(required_external),
                optional_parameters=optional_external,
            )
            # Set signature on the underlying function, not the classmethod descriptor
            ParametricSweepSource._get_data.__func__.__signature__ = signature  # type: ignore[attr-defined]

            ParametricSweepSource.__name__ = (
                name or f"{element.__name__}ParametricSweep"
            )
            assert collection_output is not None  # For mypy
            ParametricSweepSource.__doc__ = f"Parametric sweep data source for {element.__name__} producing {collection_output.__name__}."
            return ParametricSweepSource

        if element_kind == "DataOperation":
            # At this point collection_output is guaranteed to be non-None for DataOperation
            assert collection_output is not None

            class ParametricSweepOperation(DataOperation):
                _element = element
                _collection_output: Type[DataCollectionType] = collection_output  # type: ignore[assignment]
                _vars = vars
                _compiled_exprs = compiled_exprs
                _expr_src = expr_src
                _mode = mode
                _broadcast = broadcast
                _allowed_names = allowed_names
                _required_external = tuple(required_external)
                _optional_external = optional_external
                _from_context_keys = tuple(from_context_keys)
                _external_param_names = tuple(external_param_names)

                @classmethod
                def input_data_type(cls):  # type: ignore[override]
                    return cls._element.input_data_type()

                @classmethod
                def output_data_type(cls):  # type: ignore[override]
                    return cls._collection_output

                @classmethod
                def get_processing_parameter_names(cls) -> list[str]:
                    return list(cls._external_param_names)

                @classmethod
                def get_required_external_parameters(cls) -> list[str]:
                    return list(cls._from_context_keys) + list(cls._required_external)

                @classmethod
                def get_context_requirements(cls) -> list[str]:
                    return list(cls._from_context_keys)

                @classmethod
                def get_created_keys(cls) -> list[str]:
                    created = [f"{var}_values" for var in cls._vars]
                    base_created = []
                    if hasattr(cls._element, "get_created_keys"):
                        base_created = list(cls._element.get_created_keys())
                    return created + base_created

                def _process_logic(self, data, **kwargs):  # type: ignore[override]
                    sequences, created = _materialize_sequences(
                        vars=self._vars,
                        params=kwargs,
                    )

                    for key in self._from_context_keys:
                        kwargs.pop(key, None)

                    base_kwargs = {
                        name: kwargs[name]
                        for name in base_kwargs_filter
                        if name in kwargs
                    }

                    results = []
                    for sweep_args in _iterate_sweep(
                        sequences, mode=self._mode, broadcast=self._broadcast
                    ):
                        expr_outputs = {
                            out_param: fn(**sweep_args)
                            for out_param, fn in self._compiled_exprs.items()
                        }
                        call_params = _merge_call_parameters(
                            base_kwargs=base_kwargs,
                            expression_outputs=expr_outputs,
                        )
                        call_params = {
                            key: value
                            for key, value in call_params.items()
                            if key in self._allowed_names
                        }
                        element_instance = self._element(
                            context_observer=self.context_observer,
                            logger=self.logger,
                        )
                        results.append(element_instance.process(data, **call_params))

                    self._last_created_sequences = created
                    self.__class__._last_created_sequences = created
                    context_ref = getattr(self, "observer_context", None)
                    if (
                        context_ref is None
                        and getattr(self, "context_observer", None) is not None
                    ):
                        context_ref = getattr(
                            self.context_observer, "observer_context", None
                        )
                    _publish_created_context(created, context_ref)
                    return self._collection_output.from_list(results)

                @classmethod
                def _define_metadata(cls) -> dict:
                    meta = dict(super()._define_metadata())
                    meta["preprocessor"] = _preprocessor_metadata(cls)
                    meta.setdefault("component_type", "DataOperation")
                    return meta

            signature = _build_signature(
                is_classmethod=False,
                context_keys=list(from_context_keys),
                required_parameters=list(required_external),
                optional_parameters=optional_external,
            )
            # Set signature directly on the method
            ParametricSweepOperation._process_logic.__signature__ = signature  # type: ignore[attr-defined]

            ParametricSweepOperation.__name__ = (
                name or f"{element.__name__}ParametricSweep"
            )
            assert collection_output is not None  # For mypy
            ParametricSweepOperation.__doc__ = f"Parametric sweep data operation for {element.__name__} producing {collection_output.__name__}."
            return ParametricSweepOperation

        class ParametricSweepProbe(DataProbe):
            _element = element
            _vars = vars
            _compiled_exprs = compiled_exprs
            _expr_src = expr_src
            _mode = mode
            _broadcast = broadcast
            _allowed_names = allowed_names
            _required_external = tuple(required_external)
            _optional_external = optional_external
            _from_context_keys = tuple(from_context_keys)
            _external_param_names = tuple(external_param_names)

            @classmethod
            def input_data_type(cls):  # type: ignore[override]
                return cls._element.input_data_type()

            @classmethod
            def get_processing_parameter_names(cls) -> list[str]:
                return list(cls._external_param_names)

            @classmethod
            def get_required_external_parameters(cls) -> list[str]:
                return list(cls._from_context_keys) + list(cls._required_external)

            @classmethod
            def get_context_requirements(cls) -> list[str]:
                return list(cls._from_context_keys)

            @classmethod
            def get_created_keys(cls) -> list[str]:
                created = [f"{var}_values" for var in cls._vars]
                base_created = []
                if hasattr(cls._element, "get_created_keys"):
                    base_created = list(cls._element.get_created_keys())
                return created + base_created

            def _process_logic(self, data, **kwargs):  # type: ignore[override]
                sequences, created = _materialize_sequences(
                    vars=self._vars,
                    params=kwargs,
                )

                for key in self._from_context_keys:
                    kwargs.pop(key, None)

                base_kwargs = {
                    name: kwargs[name] for name in base_kwargs_filter if name in kwargs
                }

                results = []
                for sweep_args in _iterate_sweep(
                    sequences, mode=self._mode, broadcast=self._broadcast
                ):
                    expr_outputs = {
                        out_param: fn(**sweep_args)
                        for out_param, fn in self._compiled_exprs.items()
                    }
                    call_params = _merge_call_parameters(
                        base_kwargs=base_kwargs,
                        expression_outputs=expr_outputs,
                    )
                    call_params = {
                        key: value
                        for key, value in call_params.items()
                        if key in self._allowed_names
                    }
                    probe_instance = self._element(logger=self.logger)
                    results.append(probe_instance.process(data, **call_params))

                self._last_created_sequences = created
                self.__class__._last_created_sequences = created
                context_ref = getattr(self, "observer_context", None)
                if (
                    context_ref is None
                    and getattr(self, "context_observer", None) is not None
                ):
                    context_ref = getattr(
                        self.context_observer, "observer_context", None
                    )
                _publish_created_context(created, context_ref)
                return results

            @classmethod
            def _define_metadata(cls) -> dict:
                meta = dict(super()._define_metadata())
                meta["preprocessor"] = _preprocessor_metadata(cls)
                meta.setdefault("component_type", "DataProbe")
                return meta

        signature = _build_signature(
            is_classmethod=False,
            context_keys=list(from_context_keys),
            required_parameters=list(required_external),
            optional_parameters=optional_external,
        )
        # Set signature directly on the method
        ParametricSweepProbe._process_logic.__signature__ = signature  # type: ignore[attr-defined]

        ParametricSweepProbe.__name__ = name or f"{element.__name__}ParametricSweep"
        ParametricSweepProbe.__doc__ = (
            f"Parametric sweep data probe for {element.__name__}."
        )
        return ParametricSweepProbe
