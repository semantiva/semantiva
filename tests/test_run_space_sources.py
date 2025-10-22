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


def test_source_rename_single_column_yaml(tmp_path):
    """Test renaming a single column from YAML source."""
    path = tmp_path / "data.yaml"
    with path.open("w") as handle:
        yaml.safe_dump({"factor": [10, 20], "value": [1.0, 2.0]}, handle)

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                source=RunSource(
                    format="yaml",
                    path=str(path),
                    rename={"factor": "multiplier"},
                ),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    # Verify runs have renamed key
    assert len(runs) == 2
    assert runs[0] == {"multiplier": 10, "value": 1.0}
    assert runs[1] == {"multiplier": 20, "value": 2.0}

    # Verify original key is gone
    assert "factor" not in runs[0]
    assert "factor" not in runs[1]

    # Verify metadata captures rename
    assert meta["blocks"][0]["context_keys"] == ["multiplier", "value"]
    assert meta["blocks"][0]["source"]["rename"] == {"factor": "multiplier"}


def test_source_rename_multiple_columns_csv(tmp_path):
    """Test renaming multiple columns from CSV source."""
    path = _write_csv({"lr": [0.001, 0.01], "mom": [0.9, 0.95], "epochs": [10, 20]})

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                source=RunSource(
                    format="csv",
                    path=path,
                    rename={"lr": "learning_rate", "mom": "momentum"},
                ),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    # Verify all renames applied
    assert len(runs) == 2
    assert runs[0] == {"learning_rate": 0.001, "momentum": 0.9, "epochs": 10}
    assert runs[1] == {"learning_rate": 0.01, "momentum": 0.95, "epochs": 20}

    # Verify original keys are gone
    assert "lr" not in runs[0]
    assert "mom" not in runs[0]

    # Verify metadata
    assert sorted(meta["blocks"][0]["context_keys"]) == [
        "epochs",
        "learning_rate",
        "momentum",
    ]
    assert meta["blocks"][0]["source"]["rename"] == {
        "lr": "learning_rate",
        "mom": "momentum",
    }


def test_source_rename_with_select(tmp_path):
    """Test rename works correctly when combined with select."""
    path = tmp_path / "data.yaml"
    with path.open("w") as handle:
        yaml.safe_dump(
            {"a": [1, 2], "b": [10, 20], "c": [100, 200], "d": [1000, 2000]}, handle
        )

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                source=RunSource(
                    format="yaml",
                    path=str(path),
                    select=["a", "c"],  # Select only a and c
                    rename={"a": "alpha", "c": "gamma"},  # Rename selected columns
                ),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    # Verify only selected and renamed columns present
    assert len(runs) == 2
    assert runs[0] == {"alpha": 1, "gamma": 100}
    assert runs[1] == {"alpha": 2, "gamma": 200}

    # Verify non-selected columns are absent
    assert "b" not in runs[0]
    assert "d" not in runs[0]

    # Verify original selected keys are renamed
    assert "a" not in runs[0]
    assert "c" not in runs[0]

    # Verify metadata
    assert sorted(meta["blocks"][0]["context_keys"]) == ["alpha", "gamma"]


def test_source_rename_json_list_format(tmp_path):
    """Test rename with JSON list-of-objects format."""
    path = tmp_path / "params.json"
    path.write_text(
        json.dumps(
            [
                {"old_name": "value1", "keep": 100},
                {"old_name": "value2", "keep": 200},
            ]
        )
    )

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                source=RunSource(
                    format="json",
                    path=str(path),
                    rename={"old_name": "new_name"},
                ),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    assert len(runs) == 2
    assert runs[0] == {"new_name": "value1", "keep": 100}
    assert runs[1] == {"new_name": "value2", "keep": 200}
    assert "old_name" not in runs[0]


def test_source_rename_preserves_types(tmp_path):
    """Test that rename preserves value types correctly."""
    path = tmp_path / "typed.yaml"
    with path.open("w") as handle:
        yaml.safe_dump(
            {
                "int_col": [1, 2],
                "float_col": [1.5, 2.5],
                "str_col": ["a", "b"],
                "bool_col": [True, False],
            },
            handle,
        )

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="by_position",
                source=RunSource(
                    format="yaml",
                    path=str(path),
                    rename={
                        "int_col": "integers",
                        "float_col": "floats",
                        "str_col": "strings",
                        "bool_col": "booleans",
                    },
                ),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    # Verify types are preserved
    assert runs[0]["integers"] == 1
    assert isinstance(runs[0]["integers"], int)

    assert runs[0]["floats"] == 1.5
    assert isinstance(runs[0]["floats"], float)

    assert runs[0]["strings"] == "a"
    assert isinstance(runs[0]["strings"], str)

    assert runs[0]["booleans"] is True
    assert isinstance(runs[0]["booleans"], bool)


def test_source_rename_with_combinatorial_mode(tmp_path):
    """Test rename works with combinatorial expansion mode."""
    path = tmp_path / "grid.yaml"
    with path.open("w") as handle:
        yaml.safe_dump({"x_val": [1, 2], "y_val": [10, 20]}, handle)

    cfg = RunSpaceV1Config(
        blocks=[
            RunBlock(
                mode="combinatorial",
                source=RunSource(
                    format="yaml",
                    path=str(path),
                    mode="combinatorial",
                    rename={"x_val": "x", "y_val": "y"},
                ),
            )
        ]
    )

    runs, meta = expand_run_space(cfg)

    # Should create Cartesian product: 2 x 2 = 4 runs
    assert len(runs) == 4
    assert {"x": 1, "y": 10} in runs
    assert {"x": 1, "y": 20} in runs
    assert {"x": 2, "y": 10} in runs
    assert {"x": 2, "y": 20} in runs

    # Verify original names gone
    for run in runs:
        assert "x_val" not in run
        assert "y_val" not in run
