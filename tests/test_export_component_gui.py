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

from semantiva.tools import export_component_gui as ecg


def test_main_injects_script(monkeypatch, tmp_path, capsys):
    dummy_ttl = tmp_path / "components.ttl"
    dummy_ttl.write_text("@prefix smtv: <http://semantiva.org/semantiva#> .")
    output_file = tmp_path / "output.html"

    dummy_data = {"nodes": [], "edges": []}

    monkeypatch.setattr(ecg, "build_component_json", lambda path: dummy_data)
    monkeypatch.setattr(
        Path, "read_text", lambda self: "<html><body>Hello</body></html>"
    )

    written = {}

    def fake_write_text(self, content):
        written["content"] = content

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    monkeypatch.setattr(
        sys, "argv", ["export_component_gui", str(dummy_ttl), str(output_file)]
    )

    ecg.main()

    content = written.get("content", "")
    assert f"window.COMPONENT_DATA = {json.dumps(dummy_data)}" in content
    assert content.count("<script>") == 1

    captured = capsys.readouterr()
    assert f"Standalone GUI written to {output_file}" in captured.out
