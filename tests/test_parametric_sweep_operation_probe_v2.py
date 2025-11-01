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

from semantiva.data_processors.parametric_sweep_factory import (
    ParametricSweepFactory,
    RangeSpec,
)
from semantiva.examples.test_utils import (
    FloatCollectValueProbe,
    FloatDataCollection,
    FloatDataType,
    FloatMultiplyOperation,
)


def test_operation_sweep_with_collection_input():
    col = FloatDataCollection.from_list([FloatDataType(1.0), FloatDataType(3.0)])
    Sweep = ParametricSweepFactory.create(
        element=FloatMultiplyOperation,
        element_kind="DataOperation",
        collection_output=FloatDataCollection,
        vars={"f": RangeSpec(2.0, 3.0, steps=2)},
        parametric_expressions={"factor": "f"},
        mode="combinatorial",
        broadcast=False,
    )
    operation = Sweep()
    combined = []
    for item in col:
        out = operation.process(item)
        combined.extend(x.data for x in out)
    assert combined == [2.0, 3.0, 6.0, 9.0]


def test_probe_sweep_list_and_passthrough():
    Sweep = ParametricSweepFactory.create(
        element=FloatCollectValueProbe,
        element_kind="DataProbe",
        collection_output=None,
        vars={"n": RangeSpec(1, 3, steps=3)},
        parametric_expressions={},
        mode="combinatorial",
        broadcast=False,
    )
    data = FloatDataType(7.0)
    probe = Sweep()
    results = probe.process(data)
    assert results == [7.0, 7.0, 7.0]
