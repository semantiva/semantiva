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

import subprocess
import sys
from pathlib import Path
import textwrap


def run_cli(args, cwd: Path | None = None):
    cmd = [sys.executable, "-m", "semantiva.semantiva", *args]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def make_pipeline(tmp_path: Path, content: str, name: str = "pipeline.yaml") -> Path:
    path = tmp_path / name
    path.write_text(textwrap.dedent(content))
    return path


def test_cli_run_success(tmp_path: Path):
    output_file = tmp_path / "result.txt"
    yaml_path = make_pipeline(
        tmp_path,
        f"""
        pipeline:
          nodes:
            - processor: FloatMockDataSource
            - processor: FloatMultiplyOperation
              parameters:
                factor: 2.0
            - processor: FloatTxtFileSaver
              parameters:
                file_path: "{output_file}"
        """,
    )
    res = run_cli(["run", str(yaml_path)])
    assert res.returncode == 0
    assert output_file.read_text().strip() == "84.0"
    assert "Completed" in res.stdout


def test_cli_file_not_found():
    res = run_cli(["run", "missing.yaml"])
    assert res.returncode == 2


def test_cli_validate(tmp_path: Path):
    valid = make_pipeline(
        tmp_path,
        """
        pipeline:
          nodes:
            - processor: FloatMockDataSource
            - processor: FloatMultiplyOperation
              parameters:
                factor: 2.0
            - processor: FloatMockDataSink
        """,
    )
    invalid = make_pipeline(tmp_path, "pipeline:\n  bad: true\n", name="invalid.yaml")

    res_valid = run_cli(["run", str(valid), "--validate"])
    assert res_valid.returncode == 0

    res_invalid = run_cli(["run", str(invalid), "--validate"])
    assert res_invalid.returncode == 3


def test_cli_dry_run(tmp_path: Path):
    output_file = tmp_path / "should_not_exist.txt"
    yaml_path = make_pipeline(
        tmp_path,
        f"""
        pipeline:
          nodes:
            - processor: FloatMockDataSource
            - processor: FloatTxtFileSaver
              parameters:
                file_path: "{output_file}"
        """,
    )
    res = run_cli(["run", str(yaml_path), "--dry-run"])
    assert res.returncode == 0
    assert not output_file.exists()


def test_cli_runtime_fail(tmp_path: Path):
    yaml_path = make_pipeline(
        tmp_path,
        """
        pipeline:
          nodes:
            - processor: FloatMockDataSource
            - processor: FloatDivideOperation
              parameters:
                divisor: 0
        """,
    )
    res = run_cli(["run", str(yaml_path)])
    assert res.returncode == 4


def test_cli_overrides(tmp_path: Path):
    output_file = tmp_path / "override.txt"
    yaml_path = make_pipeline(
        tmp_path,
        f"""
        pipeline:
          nodes:
            - processor: FloatMockDataSource
            - processor: FloatMultiplyOperation
              parameters:
                factor: 2.0
            - processor: FloatTxtFileSaver
              parameters:
                file_path: "{output_file}"
        """,
    )
    res_ok = run_cli(
        [
            "run",
            str(yaml_path),
            "--set",
            "pipeline.nodes.1.parameters.factor=3.0",
        ]
    )
    assert res_ok.returncode == 0
    assert output_file.read_text().strip() == "126.0"

    res_bad = run_cli(
        [
            "run",
            str(yaml_path),
            "--set",
            "pipeline.nodes.9.parameters.factor=5",
        ]
    )
    assert res_bad.returncode == 3


def test_cli_argument_error():
    res = run_cli(["run"])
    assert res.returncode == 1
