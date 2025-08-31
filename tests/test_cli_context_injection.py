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

"""
CLI context injection tests.

Tests that the `semantiva run --context` flag properly injects context
values, verifying injection via the specific "Injected context:" debug message.
"""

from pathlib import Path
from .test_utils import run_cli


def test_cli_run_with_context(tmp_path: Path):
    yaml = """
pipeline:
  nodes:
    - processor: FloatValueDataSource
    - processor: ModelFittingContextProcessor
      parameters:
        fitting_model: "model:PolynomialFittingModel:degree=1"
"""
    p = tmp_path / "fit.yaml"
    p.write_text(yaml)
    res = run_cli(
        [
            "run",
            str(p),
            "--context",
            "x_values=[0.0,1.0]",
            "--context",
            "y_values=[1.0,2.0]",
            "-v",  # Enable verbose logging to see context injection
        ]
    )
    assert res.returncode == 0
    # Verify context injection worked by checking for the specific debug message
    assert "Injected context:" in res.stdout and "[0.0, 1.0]" in res.stdout
