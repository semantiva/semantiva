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

import pytest

from semantiva.configurations.schema import RunBlock, RunSpaceV1Config
from semantiva.execution.run_space import expand_run_space
from semantiva.exceptions.pipeline_exceptions import (
    PipelineConfigurationError as ConfigurationError,
)


def test_run_space_single_zip_block():
    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(mode="by_position", context={"a": [1, 2, 3], "b": [10, 20, 30]})
        ]
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 3
    assert runs[1] == {"a": 2, "b": 20}
    assert meta["blocks"][0]["mode"] == "by_position"
    assert meta["blocks"][0]["size"] == 3


def test_run_space_product_block():
    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(mode="combinatorial", context={"x": [1, 2], "y": [10, 20, 30]})
        ]
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 6
    assert {"x": 2, "y": 20} in runs
    assert meta["blocks"][0]["mode"] == "combinatorial"
    assert meta["expanded_runs"] == 6


def test_run_space_multi_block_product_combine():
    cfg = RunSpaceV1Config(
        combine="combinatorial",
        blocks=[
            RunBlock(
                mode="by_position",
                context={"lr": [0.001, 0.01], "momentum": [0.9, 0.95]},
            ),
            RunBlock(
                mode="combinatorial", context={"batch_size": [16, 32], "seed": [1, 2]}
            ),
        ],
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 8
    assert meta["expanded_runs"] == 8
    assert runs[3]["batch_size"] == 32
    assert all("lr" in run and "seed" in run for run in runs)


def test_run_space_zip_combine_requires_equal_sizes():
    cfg = RunSpaceV1Config(
        combine="by_position",
        blocks=[
            RunBlock(mode="by_position", context={"a": [1, 2, 3]}),
            RunBlock(mode="by_position", context={"b": [10, 20]}),
        ],
    )

    with pytest.raises(ConfigurationError):
        expand_run_space(cfg)


def test_deterministic_order_of_runs():
    cfg = RunSpaceV1Config(
        combine="combinatorial",
        blocks=[
            RunBlock(mode="combinatorial", context={"b": [2, 1], "a": [1]}),
            RunBlock(mode="combinatorial", context={"d": [0], "c": [3, 2]}),
        ],
    )

    runs, _ = expand_run_space(cfg)

    assert runs == [
        {"a": 1, "b": 2, "c": 3, "d": 0},
        {"a": 1, "b": 2, "c": 2, "d": 0},
        {"a": 1, "b": 1, "c": 3, "d": 0},
        {"a": 1, "b": 1, "c": 2, "d": 0},
    ]
