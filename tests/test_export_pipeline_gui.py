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

import sys
import json
from pathlib import Path
import pytest

from semantiva.tools import export_pipeline_gui as epg


class DummyPipeline:
    pass


def test_main_injects_script(monkeypatch, tmp_path, capsys):
    # Prepare dummy input YAML and output path
    dummy_yaml = tmp_path / "pipeline.yaml"
    dummy_yaml.write_text("dummy: config")
    output_file = tmp_path / "output.html"

    # Dummy pipeline data
    dummy_data = {"foo": "bar"}

    # Monkeypatch dependent functions
    monkeypatch.setattr(epg, "load_pipeline_from_yaml", lambda path: {"dummy": True})
    monkeypatch.setattr(epg, "Pipeline", lambda config: DummyPipeline())
    monkeypatch.setattr(epg, "build_pipeline_json", lambda pipeline: dummy_data)

    # Monkeypatch reading template HTML
    monkeypatch.setattr(
        Path, "read_text", lambda self: "<html><body>Hello</body></html>"
    )

    # Capture written content
    written = {}

    def fake_write_text(self, content):
        written["content"] = content

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    # Set command-line arguments
    monkeypatch.setattr(
        sys, "argv", ["export_pipeline_gui", str(dummy_yaml), str(output_file)]
    )

    # Run main
    epg.main()

    # Verify that the script injection contains the pipeline data
    content = written.get("content", "")
    assert "window.PIPELINE_DATA = %s" % json.dumps(dummy_data) in content
    assert content.count("<script>") == 1

    # Verify output message
    captured = capsys.readouterr()
    assert f"Standalone GUI written to {output_file}" in captured.out
