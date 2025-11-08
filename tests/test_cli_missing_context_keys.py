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

import textwrap
from pathlib import Path


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_cli_reports_all_missing_context_keys_once_preflight(tmp_path, capsys):
    """Run the CLI _run function in-process and assert it reports all missing keys at once.

    This avoids subprocess environment/extension loading issues by executing the CLI
    logic in the same test process (so registry and extensions are available).
    """
    pipeline_yaml = textwrap.dedent(
        """
        extensions: ["semantiva-examples"]

        pipeline:
            nodes:
                - processor: FloatValueDataSource
                - processor: FloatMultiplyOperation
                - processor: FloatAddOperation
                - processor: FloatMockDataSink
        """
    ).strip()

    cfg = _write(tmp_path, "p.yaml", pipeline_yaml)

    # Import CLI helpers locally so test import doesn't run heavy initialization at module import time
    from semantiva.cli import _parse_args, _run, EXIT_CONFIG_ERROR

    args = _parse_args(["run", str(cfg)])

    # Run the CLI handler in-process and capture stderr
    rc = _run(args)
    captured = capsys.readouterr()
    stderr = captured.err.lower()

    # Should fail before any execution, listing ALL missing keys
    assert rc == EXIT_CONFIG_ERROR
    for key in ["addend", "factor", "path"]:
        assert key in stderr
    assert "missing required context keys" in stderr
