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


def test_cli_inspect_missing_file():
    res = run_cli(["inspect", "missing.yaml"])
    assert res.returncode == 2


def test_cli_inspect_invalid_yaml(tmp_path: Path):
    invalid = make_pipeline(tmp_path, "pipeline: [bad")
    res = run_cli(["inspect", str(invalid)])
    assert res.returncode == 3
