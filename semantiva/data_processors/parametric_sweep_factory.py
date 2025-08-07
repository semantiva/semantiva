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

from typing import Any, Dict, Tuple, Type, Sequence

import numpy as np

from semantiva.data_io.data_io import DataSource
from semantiva.data_processors.data_processors import DataOperation
from semantiva.data_types import NoDataType, DataCollectionType


class ParametricSweepFactory:
    """Factory for creating parametric sweep data operations."""

    @staticmethod
    def create(
        element_source: Type[DataSource],
        collection_output: Type[DataCollectionType],
        independent_vars: Dict[str, Tuple[float, float]],
        parametric_expressions: Dict[str, str],
        num_steps: int,
        static_params: Dict[str, Any] | None = None,
        name: str | None = None,
    ) -> Type[DataOperation]:
        """Create a parametric sweep data operation."""

        if not issubclass(element_source, DataSource):
            raise TypeError("element_source must be a DataSource subclass")
        if not issubclass(collection_output, DataCollectionType):
            raise TypeError("collection_output must be a DataCollectionType subclass")
        if not independent_vars:
            raise ValueError("independent_vars must be non-empty")
        if num_steps <= 1:
            raise ValueError("num_steps must be greater than 1")

        class_name = name or f"{element_source.__name__}ParametricSweep"

        class ParametricSweep(DataOperation):
            """Dynamically created parametric sweep operation."""

            _element_source = element_source
            _collection_output = collection_output
            _independent_vars = independent_vars
            _parametric_expressions = parametric_expressions
            _num_steps = num_steps
            _static_params = static_params or {}

            @classmethod
            def input_data_type(cls) -> Type[NoDataType]:
                """Return the input data type for this operation."""
                return NoDataType

            @classmethod
            def output_data_type(cls) -> Type[DataCollectionType]:
                """Return the output data type for this operation."""
                return cls._collection_output

            @classmethod
            def get_created_keys(cls) -> list[str]:
                """Return the keys that this operation creates in the context."""
                return [f"{var}_values" for var in cls._independent_vars]

            def _process_logic(
                self, data: NoDataType, *args, **kwargs
            ) -> DataCollectionType:
                """Process the parametric sweep by generating sequences and evaluating expressions."""
                sequences = {
                    var: np.linspace(lo, hi, self._num_steps)
                    for var, (lo, hi) in self._independent_vars.items()
                }
                for var, seq in sequences.items():
                    self._notify_context_update(f"{var}_values", seq)

                # names of the sweep variables, e.g. "t, x, y"
                arg_list = ", ".join(self._independent_vars.keys())
                funcs = {
                    name: eval(f"lambda {arg_list}: {expr}", {}, {})
                    for name, expr in self._parametric_expressions.items()
                }

                elements = []
                for i in range(self._num_steps):
                    current = {var: sequences[var][i] for var in sequences}
                    dynamic = {name: func(**current) for name, func in funcs.items()}
                    params = {**self._static_params, **dynamic}
                    elements.append(self._element_source.get_data(**params))
                return self._collection_output(elements)

        ParametricSweep.__name__ = class_name
        ParametricSweep.__doc__ = (
            f"Parametric sweep data operation for {element_source.__name__} "
            f"producing {collection_output.__name__}."
        )

        return ParametricSweep
