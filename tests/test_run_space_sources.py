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

import csv
import json
import tempfile

import pytest
import yaml

from semantiva.configurations.schema import RunBlock, RunSource, RunSpaceV1Config
from semantiva.execution.run_space import expand_run_space
from semantiva.exceptions.pipeline_exceptions import (
    PipelineConfigurationError as ConfigurationError,
)


def _write_csv(columns: dict[str, list[object]]) -> str:
    handle = tempfile.NamedTemporaryFile("w", newline="", delete=False, suffix=".csv")
    writer = csv.DictWriter(handle, fieldnames=list(columns.keys()))
    writer.writeheader()
    for row_idx in range(len(next(iter(columns.values()), []))):
        writer.writerow({key: columns[key][row_idx] for key in columns})
    handle.close()
    return handle.name


def test_csv_source_rows_are_runs_zip(tmp_path):
    path = _write_csv({"lr": [0.001, 0.01], "momentum": [0.9, 0.95]})
    cfg = RunSpaceV1Config(
        blocks=[RunBlock(mode="by_position", source=RunSource(format="csv", path=path))]
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 2
    assert runs[1]["momentum"] == pytest.approx(0.95)
    assert meta["blocks"][0]["source"]["format"] == "csv"
    assert "sha256" in meta["blocks"][0]["source"]


def test_json_list_rows_zip(tmp_path):
    path = tmp_path / "params.json"
    path.write_text(
        json.dumps([{"seed": 1, "profile": "a"}, {"seed": 2, "profile": "b"}])
    )
    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position", source=RunSource(format="json", path=str(path))
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 2
    assert runs[0]["seed"] == 1
    assert meta["blocks"][0]["source"]["mode"] == "by_position"


def test_yaml_product_source(tmp_path):
    path = tmp_path / "grid.yaml"
    with path.open("w") as handle:
        yaml.safe_dump({"x": [1, 2], "y": [10, 20, 30]}, handle)
    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="combinatorial",
                source=RunSource(format="yaml", path=str(path), mode="combinatorial"),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 6
    assert meta["blocks"][0]["source"]["mode"] == "combinatorial"


def test_source_rename_collision(tmp_path):
    path = tmp_path / "rename.yaml"
    with path.open("w") as handle:
        yaml.safe_dump({"x": [1, 2], "y": [3, 4]}, handle)

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                source=RunSource(
                    format="yaml",
                    path=str(path),
                    rename={"x": "shared", "y": "shared"},
                ),
            )
        ]
    )

    with pytest.raises(ConfigurationError) as exc:
        expand_run_space(cfg)

    assert "run_space source rename collision for 'y' -> 'shared'" in str(exc.value)
