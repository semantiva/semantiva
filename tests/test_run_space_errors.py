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

import json

import pytest
import yaml

from semantiva.configurations.schema import RunBlock, RunSource, RunSpaceV1Config
from semantiva.execution.run_space import expand_run_space
from semantiva.exceptions.pipeline_exceptions import (
    PipelineConfigurationError as ConfigurationError,
    RunSpaceMaxRunsExceededError,
)


def test_duplicate_keys_across_blocks_raises():
    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(mode="combinatorial", context={"a": [1, 2]}),
            RunBlock(mode="by_position", context={"a": [3, 4]}),
        ]
    )

    with pytest.raises(ConfigurationError) as exc:
        expand_run_space(cfg)

    message = str(exc.value)
    assert "Duplicate context key(s) across blocks: ['a']" in message
    assert "(at index 1)" in message


def test_zip_block_mismatched_lengths():
    cfg = RunSpaceV1Config(
        blocks=[RunBlock(mode="by_position", context={"x": [1], "y": [1, 2]})]
    )

    with pytest.raises(ConfigurationError) as exc:
        expand_run_space(cfg)

    assert "by_position block requires identical list lengths" in str(exc.value)


def test_cap_exceeded():
    cfg = RunSpaceV1Config(
        max_runs=2,
        blocks=[RunBlock(mode="combinatorial", context={"x": [1, 2], "y": [10, 20]})],
    )

    with pytest.raises(RunSpaceMaxRunsExceededError):
        expand_run_space(cfg)


def test_duplicate_within_block_between_context_and_source(tmp_path):
    path = tmp_path / "values.json"
    path.write_text(json.dumps([{"a": 10}, {"a": 20}]))
    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                context={"a": [1, 2]},
                source=RunSource(format="json", path=str(path)),
            )
        ]
    )

    with pytest.raises(ConfigurationError) as exc:
        expand_run_space(cfg)

    assert "Duplicate context key(s) within block (context vs source): ['a']" in str(
        exc.value
    )


def test_combine_zip_mismatch_sizes_message():
    cfg = RunSpaceV1Config(
        combine="by_position",
        blocks=[
            RunBlock(mode="by_position", context={"a": [1, 2]}),
            RunBlock(mode="combinatorial", context={"b": [0, 1, 2]}),
        ],
    )

    with pytest.raises(ConfigurationError) as exc:
        expand_run_space(cfg)

    assert "combine=by_position requires equal block sizes; got [2, 3]" in str(
        exc.value
    )


def test_rename_collision_with_context_fails(tmp_path):
    source_path = tmp_path / "source.yaml"
    source_path.write_text(yaml.safe_dump({"x": [1, 2]}))

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                context={"y": [10, 20]},
                source=RunSource(
                    format="yaml",
                    path=str(source_path),
                    mode="combinatorial",
                    rename={"x": "y"},
                ),
            )
        ]
    )

    with pytest.raises(ConfigurationError) as exc:
        expand_run_space(cfg)

    assert "Duplicate context key(s) within block (context vs source): ['y']" in str(
        exc.value
    )
