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

from pathlib import Path

from .test_cli import make_pipeline, run_cli


def test_cli_run_context(tmp_path: Path):
    output_file = tmp_path / "ctx.txt"
    yaml_path = make_pipeline(
        tmp_path,
        """
        pipeline:
          nodes:
            - processor: FloatValueDataSource
            - processor: FloatMultiplyOperation
              parameters:
                factor: 2.0
            - processor: FloatTxtFileSaver
        """,
    )
    res = run_cli(["run", str(yaml_path), "--context", f"path={output_file}"])
    assert res.returncode == 0
    assert output_file.read_text().strip() == "84.0"


def test_cli_run_context_invalid(tmp_path: Path):
    yaml_path = make_pipeline(
        tmp_path,
        """
        pipeline:
          nodes:
            - processor: FloatValueDataSource
        """,
    )
    res = run_cli(["run", str(yaml_path), "--context", "bad"])
    assert res.returncode == 3
